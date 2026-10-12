#!/usr/bin/env escript
-mode(compile).
main(_) ->
    {ok,gossip_sim,B}=compile:file("src/gossip_sim.erl",[binary,report_errors]),
    {module,gossip_sim}=code:load_binary(gossip_sim,"src/gossip_sim.erl",B),
    9=gossip_sim:actual_nodes(5,grid),
    5=gossip_sim:actual_nodes(5,line),
    #{1:=[2],2:=[1,3],3:=[2]}=gossip_sim:neighbors(3,line),
    Grid=gossip_sim:neighbors(9,grid),
    [4,2]=maps:get(1,Grid),
    [2,8,4,6]=maps:get(5,Grid),
    rand:seed(exsss,{1,2,3}), Imp=gossip_sim:neighbors(9,imp_grid),
    lists:foreach(fun(I)->Ns=maps:get(I,Imp),true=length(Ns)=:=length(maps:get(I,Grid))+1,
        false=lists:member(I,Ns),true=length(Ns)=:=length(lists:usort(Ns)) end,lists:seq(1,9)),
    lists:foreach(fun(T)->
        G=gossip_sim:run(9,T,gossip,#{seed=>17,timeout=>3000}),converged=maps:get(status,G),9=maps:get(reached,G),
        P=gossip_sim:run(9,T,push_sum,#{seed=>17,timeout=>3000,termination=>global}),converged=maps:get(status,P),9=maps:get(stable,P),
        true=maps:get(max_error,P)<1.0e-7
    end,[full,line,grid,imp_grid]),
    Strict=gossip_sim:run(16,full,push_sum,#{seed=>17,timeout=>3000}),
    converged=maps:get(status,Strict),1=maps:get(stable,Strict),
    lists:foreach(fun(A)->R=gossip_sim:run(1,full,A,#{timeout=>1000}),converged=maps:get(status,R) end,[gossip,push_sum]),
    Timeout=gossip_sim:run(100,line,gossip,#{timeout=>0}),timeout=maps:get(status,Timeout),
    io:format("All topology, algorithm, singleton, and timeout checks passed.~n").
