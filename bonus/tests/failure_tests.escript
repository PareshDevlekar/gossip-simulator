#!/usr/bin/env escript
-mode(compile).
main(_) ->
    {ok,bonus_sim,B}=compile:file("src/bonus_sim.erl",[binary,report_errors]),
    {module,bonus_sim}=code:load_binary(bonus_sim,"src/bonus_sim.erl",B),
    Adj=bonus_sim:neighbors(4,line),
    {Zero,3}=bonus_sim:failed_links(4,Adj,0.0),0=map_size(Zero),
    {All,3}=bonus_sim:failed_links(4,Adj,1.0),3=map_size(All),
    true=maps:is_key({1,2},All),true=maps:is_key({2,3},All),true=maps:is_key({3,4},All),
    rand:seed(exsss,{1,2,3}),{F1,_}=bonus_sim:failed_links(16,bonus_sim:neighbors(16,full),0.3),
    rand:seed(exsss,{1,2,3}),{F2,_}=bonus_sim:failed_links(16,bonus_sim:neighbors(16,full),0.3),F1=F2,
    Before=erlang:system_info(process_count),
    lists:foreach(fun(T)->
        lists:foreach(fun(A)->
            Good=bonus_sim:run(9,T,A,#{timeout=>2000,seed=>17,failure_probability=>0.0}),
            converged=maps:get(status,Good),0=maps:get(dropped,Good),0=maps:get(failed_links,Good),
            Bad=bonus_sim:run(9,T,A,#{timeout=>20,seed=>17,failure_probability=>1.0}),
            timeout=maps:get(status,Bad),1=maps:get(reached,Bad),
            true=maps:get(dropped,Bad)>0,
            true=maps:get(sent,Bad)=:=maps:get(dropped,Bad)
        end,[gossip,push_sum])
    end,[full,line,grid,imp_grid]),
    Single=bonus_sim:run(1,full,push_sum,#{timeout=>1000,failure_probability=>1.0}),
    converged=maps:get(status,Single),0=maps:get(total_links,Single),0=maps:get(dropped,Single),
    timer:sleep(20),After=erlang:system_info(process_count),true=After=<Before+2,
    io:format("Failure endpoints, reproducibility, all topologies/algorithms, singleton and cleanup checks passed.~n").
