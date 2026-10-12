-module(gossip_sim).
-export([main/1, run/4, neighbors/2, actual_nodes/2]).

main([N0,T0,A0]) ->
    try
        N = list_to_integer(N0), true = N > 0,
        T = topology(T0), A = algorithm(A0),
        Timeout = env_int("PROJECT2_TIMEOUT_MS", 30000),
        Seed = env_int("PROJECT2_SEED", 42),
        Mode = case os:getenv("PROJECT2_TERMINATION") of false -> strict; "strict" -> strict; "global" -> global end,
        R = run(N,T,A,#{timeout=>Timeout,seed=>Seed,termination=>Mode}),
        io:format("status=~s requested=~B nodes=~B topology=~s algorithm=~s time_us=~B reached=~B stable=~B max_error=~.12g seed=~B termination=~s~n",
          [maps:get(status,R),N,maps:get(nodes,R),T0,A0,maps:get(time_us,R),maps:get(reached,R),maps:get(stable,R),maps:get(max_error,R),Seed,Mode]),
        case maps:get(status,R) of converged -> halt(0); _ -> halt(2) end
    catch _:_ -> io:format(standard_error,"Usage: project2 numNodes {full|2D|line|imp2D} {gossip|push-sum}~n",[]), halt(1)
    end;
main(_) -> io:format(standard_error,"Usage: project2 numNodes {full|2D|line|imp2D} {gossip|push-sum}~n",[]),halt(1).
topology("full") -> full; topology("2D") -> grid; topology("line") -> line; topology("imp2D") -> imp_grid.
algorithm("gossip") -> gossip; algorithm("push-sum") -> push_sum.
env_int(Name, Default) -> case os:getenv(Name) of false -> Default; V -> list_to_integer(V) end.
actual_nodes(N,T) when T=:=grid; T=:=imp_grid -> K=ceil(math:sqrt(N)), K*K;
actual_nodes(N,_) -> N.
neighbors(N,full) -> maps:from_list([{I,{full,N,I}} || I <- lists:seq(1,N)]);
neighbors(N,line) -> maps:from_list([{I,[J || J <- [I-1,I+1],J>=1,J=<N]} || I <- lists:seq(1,N)]);
neighbors(N,T) when T=:=grid; T=:=imp_grid ->
    K=round(math:sqrt(N)),
    maps:from_list([{I,grid_neighbors(I,N,K,T)} || I <- lists:seq(1,N)]).
grid_neighbors(I,N,K,T) ->
    Base=[J || {J,Valid} <- [{I-K,I>K},{I+K,I+K=<N},{I-1,(I-1) rem K>0},{I+1,I rem K>0}],Valid],
    case T=:=imp_grid andalso N>length(Base)+1 of
        true -> Base ++ [extra(I,N,Base)]; false -> Base
    end.
extra(I,N,Base) -> J=rand:uniform(N), case J=:=I orelse lists:member(J,Base) of true -> extra(I,N,Base); false -> J end.

run(Requested,T,A,Opts) ->
    N=actual_nodes(Requested,T), Seed=maps:get(seed,Opts,42), Mode=maps:get(termination,Opts,strict),
    rand:seed(exsss,{Seed+1,Seed+2,Seed+3}), Adj=neighbors(N,T), Parent=self(), Ref=make_ref(),
    Ps=list_to_tuple([spawn_monitor(fun()->init(Parent,Ref,I,A,Seed,Mode) end) || I <- lists:seq(1,N)]),
    Pids=list_to_tuple([P || {P,_} <- tuple_to_list(Ps)]),
    lists:foreach(fun(I)->element(I,Pids)!{setup,maps:get(I,Adj),Pids} end,lists:seq(1,N)),
    ready(N,Ref),
    Start=erlang:monotonic_time(microsecond),
    element(rand:uniform(N),Pids)!start,
    Deadline=Start+maps:get(timeout,Opts,30000)*1000,
    try collect(N,{A,Mode},Ref,Start,Deadline,#{},#{},(N+1)/2) of
        Result -> Result#{nodes=>N}
    after
        lists:foreach(fun({P,M})->exit(P,kill),erlang:demonitor(M,[flush]) end,tuple_to_list(Ps)),
        flush(Ref)
    end.
ready(0,_) -> ok;
ready(N,R) -> receive {R,ready}->ready(N-1,R) after 10000 -> error(setup_timeout) end.
flush(R) -> receive {R,_,_}->flush(R); {R,_,_,_}->flush(R) after 0 -> ok end.
collect(N,A,R,Start,Deadline,Seen,Stable,Expected) ->
    Done=case A of {gossip,_} -> map_size(Seen)=:=N; {push_sum,strict} -> map_size(Stable)>0; {push_sum,global} -> map_size(Stable)=:=N end,
    case Done of
        true -> result(converged,Start,Seen,Stable,Expected);
        false ->
            Remaining=max(0,(Deadline-erlang:monotonic_time(microsecond)+999) div 1000),
            receive
                {R,seen,I} -> collect(N,A,R,Start,Deadline,Seen#{I=>true},Stable,Expected);
                {R,stable,I,Ratio} -> collect(N,A,R,Start,Deadline,Seen,Stable#{I=>Ratio},Expected);
                {R,unstable,I} -> collect(N,A,R,Start,Deadline,Seen,maps:remove(I,Stable),Expected);
                {'DOWN',_,process,_,normal} -> collect(N,A,R,Start,Deadline,Seen,Stable,Expected);
                {'DOWN',_,process,_,Reason} -> error({actor_failed,Reason})
            after Remaining -> result(timeout,Start,Seen,Stable,Expected)
            end
    end.
result(Status,Start,Seen,Stable,Expected) ->
    Err=lists:foldl(fun(X,M)->max(abs(X-Expected),M) end,0.0,maps:values(Stable)),
    #{status=>Status,time_us=>erlang:monotonic_time(microsecond)-Start,reached=>map_size(Seen),stable=>map_size(Stable),max_error=>Err}.
init(Parent,Ref,I,A,Seed,Mode) ->
    rand:seed(exsss,{Seed+I,Seed+I*17,Seed+I*101}),
    receive {setup,Ns,Ps} ->
        Parent!{Ref,ready},
        S=#{parent=>Parent,ref=>Ref,id=>I,neighbors=>Ns,pids=>Ps,termination=>Mode,count=>0,s=>float(I),w=>1.0,rounds=>0,stable=>false},
        case A of gossip -> gossip(S); push_sum -> push_sum(S) end
    end.
pick(#{neighbors:={full,1,_}}) -> self();
pick(#{neighbors:={full,N,I},pids:=Ps}) -> J=rand:uniform(N-1),element(case J>=I of true->J+1; false->J end,Ps);
pick(#{neighbors:=[],pids:=_}) -> self();
pick(#{neighbors:=Ns,pids:=Ps}) -> element(lists:nth(rand:uniform(length(Ns)),Ns),Ps).
event(S,Type) -> maps:get(parent,S)!{maps:get(ref,S),Type,maps:get(id,S)}.
gossip(S) ->
    receive
        start -> self()!rumor,gossip(S);
        rumor ->
            C=maps:get(count,S),
            case C of 0 -> event(S,seen),self()!tick; _ -> ok end,
            gossip(S#{count=>min(C+1,10)});
        tick ->
            case maps:get(count,S)<10 of
                true -> pick(S)!rumor,erlang:send_after(1,self(),tick);
                false -> ok
            end,
            gossip(S)
    end.
%% An actor terminates after three consecutive stable receptions, exactly as
%% specified in strict mode. Global mode retains stable mailbox endpoints
%% until every actor is stable, conserving mass and revoking unstable reports.
push_sum(S) ->
    receive
        start -> self()!{mass,0.0,0.0},push_sum(S);
        {mass,IncomingS,IncomingW} ->
            case maps:get(count,S) of 0->event(S,seen); _->ok end,
            Old=maps:get(s,S)/maps:get(w,S),
            Sum=maps:get(s,S)+IncomingS, W=maps:get(w,S)+IncomingW, Ratio=Sum/W,
            Rounds=case abs(Ratio-Old)<1.0e-10 of true->maps:get(rounds,S)+1; false->0 end,
            Stable=Rounds>=3, Was=maps:get(stable,S),
            case {Was,Stable} of
                {false,true}->maps:get(parent,S)!{maps:get(ref,S),stable,maps:get(id,S),Ratio};
                {true,false}->event(S,unstable);
                {true,true}->maps:get(parent,S)!{maps:get(ref,S),stable,maps:get(id,S),Ratio};
                _->ok
            end,
            Next=S#{s=>Sum/2,w=>W/2,rounds=>Rounds,stable=>Stable,count=>1},
            case Stable andalso maps:get(termination,S)=:=strict of
                true -> ok;
                false -> pick(S)!{mass,Sum/2,W/2},push_sum(Next)
            end
    end.
