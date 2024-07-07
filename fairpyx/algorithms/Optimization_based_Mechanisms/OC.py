"""
    "Optimization-based Mechanisms for the Course Allocation Problem", by Hoda Atef Yekta, Robert Day (2020)
     https://doi.org/10.1287/ijoc.2018.0849

    Programmer: Tamar Bar-Ilan, Moriya Ester Ohayon, Ofek Kats
"""

import cvxpy
import concurrent.futures
import time
from fairpyx import Instance, AllocationBuilder, ExplanationLogger
import logging
import cvxpy as cp
import numpy as np
import fairpyx.algorithms.Optimization_based_Mechanisms.optimal_functions as optimal
logger = logging.getLogger(__name__)


def OC_function(alloc: AllocationBuilder, explanation_logger: ExplanationLogger = ExplanationLogger()):
    """
    Algorethem 5: Allocate the given items to the given agents using the OC protocol.

    in the OC algorithm for CAP, we maximize ordinal utility followed by maximizing cardinal utility among rank-maximal
    solutions, performing this two-part optimization once for the whole market.

    :param alloc: an allocation builder, which tracks the allocation and the remaining capacity for items and agents of
     the fair course allocation problem(CAP).

    >>> from fairpyx.adaptors import divide
    >>> s1 = {"c1": 44, "c2": 39, "c3": 17}
    >>> s2 = {"c1": 50, "c2": 45, "c3": 5}
    >>> agent_capacities = {"s1": 2, "s2": 2}                                 # 4 seats required
    >>> course_capacities = {"c1": 2, "c2": 1, "c3": 2}                       # 5 seats available
    >>> valuations = {"s1": s1, "s2": s2}
    >>> instance = Instance(agent_capacities=agent_capacities, item_capacities=course_capacities, valuations=valuations)
    >>> divide(OC_function, instance=instance)
    {'s1': ['c1', 'c3'], 's2': ['c1', 'c2']}
    """

    startime = time.time()
    explanation_logger.info("\nAlgorithm OC starts.\n")

    x = cvxpy.Variable((len(alloc.remaining_items()), len(alloc.remaining_agents())), boolean=True)

    rank_mat = optimal.createRankMat(alloc,logger)
    sum_rank = optimal.sumOnRankMat(alloc, rank_mat, x)
    objective_Z1 = cp.Maximize(sum_rank)

    constraints_Z1 = optimal.notExceedtheCapacity(x,alloc) + optimal.numberOfCourses(x, alloc, alloc.remaining_agent_capacities)

    problem = cp.Problem(objective_Z1, constraints=constraints_Z1)
    result_Z1 = problem.solve()
    logger.info("\nRank optimization: result_Z1 = %s, x = \n%s", result_Z1, x.value)

    x = cvxpy.Variable((len(alloc.remaining_items()), len(alloc.remaining_agents())), boolean=True)  # Is there a func which zero all the matrix?
    sum_rank = optimal.sumOnRankMat(alloc, rank_mat, x)
    objective_Z2 = cp.Maximize(cp.sum([alloc.effective_value(student, course) * x[j, i]
                                        for j, course in enumerate(alloc.remaining_items())
                                        for i, student in enumerate(alloc.remaining_agents())
                                        if (student, course) not in alloc.remaining_conflicts]))

    # condition number 19:
    constraints_Z2 = optimal.notExceedtheCapacity(x, alloc) + optimal.numberOfCourses(x, alloc, alloc.remaining_agent_capacities)

    constraints_Z2.append(sum_rank == result_Z1)

    list_courses = []
    for course in alloc.remaining_items():
        list_courses.append(course)

    # logger.info("type(alloc.instance.item_conflicts) = %s ", type(alloc.instance.item_conflicts))
    logger.info("alloc.remaining_conflicts = %s ", alloc.remaining_conflicts)
    logger.info("alloc.remaining_instance().item_conflicts(c1) = %s ", alloc.remaining_instance().item_conflicts("c1"))

    #with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:

    for course in alloc.remaining_items():
        list_of_conflict = alloc.remaining_instance().item_conflicts(course)

        for course2 in list_of_conflict:
            index_c1 = list_courses.index(course)
            index_c2 = list_courses.index(course2)
            for i in range(len(alloc.remaining_agents())):
                constraints_Z2.append(x[index_c1, i] + x[index_c2, i] <= 1)

    try:
        problem = cp.Problem(objective_Z2, constraints=constraints_Z2)
        result_Z2 = problem.solve()
        logger.info("\nValue optimization: result_Z2 = %s, x = \n%s", result_Z2, x.value)

        # Check if the optimization problem was successfully solved
        if result_Z2 is not None:
            optimal.give_items_according_to_allocation_matrix(alloc, x, logger)
            #optimal.give_items_according_to_allocation_matrix_threaded(alloc, x, logger, executor, num_threads=4)

            optimal_value = problem.value
            explanation_logger.info("Optimal Objective Value:", optimal_value)
            # Now you can use this optimal value for further processing
        else:
            explanation_logger.info("Solver failed to find a solution or the problem is infeasible/unbounded.")
            raise ValueError("Solver failed to find a solution or the problem is infeasible/unbounded.")

    except Exception as e:
        explanation_logger.info("Solver failed: %s", str(e))
        logger.error("An error occurred: %s", str(e))
        raise

    logger.info("time: %s", time.time()-startime)

if __name__ == "__main__":
    import doctest, sys
    print("\n", doctest.testmod(), "\n")
    # sys.exit(1)

    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG)
    import fairpyx
    from fairpyx.adaptors import divide

    valuations =  {
        's1': {'c1': 1, 'c2': 4, 'c3': 5, 'c4': 2, 'c5': 18}, 
        's2': {'c1': 1, 'c2': 4, 'c3': 3, 'c4': 2, 'c5': 20}, 
        's3': {'c1': 3, 'c2': 5, 'c3': 3, 'c4': 2, 'c5': 17}, 
        's4': {'c1': 2, 'c2': 1, 'c3': 6, 'c4': 2, 'c5': 19}, 
        's5': {'c1': 2, 'c2': 5, 'c3': 3, 'c4': 2, 'c5': 19}
    }
    agent_capacities = {'s1': 3, 's2': 3, 's3': 3, 's4': 3, 's5': 3}
    item_capacities = {'c1': 5, 'c2': 5, 'c3': 5, 'c4': 5, 'c5': 5}
    instance = fairpyx.Instance(valuations=valuations, agent_capacities=agent_capacities, item_capacities=item_capacities)
    allocation = fairpyx.divide(OC_function, instance=instance)
    fairpyx.validate_allocation(instance, allocation, title=f"OC_function")


    # for i in range(100):
    #     np.random.seed(i)
    #     instance = fairpyx.Instance.random_uniform(
    #         num_of_agents=5, num_of_items=5, normalized_sum_of_values=30,
    #         agent_capacity_bounds=[2,6],
    #         item_capacity_bounds=[20,40],
    #         item_base_value_bounds=[1,10],
    #         item_subjective_ratio_bounds=[0.5, 1.5]
    #         )
    #     print("instance: ",instance)
    #     print("valuations: ",instance._valuations)
    #     allocation = fairpyx.divide(fairpyx.algorithms.OC_function, instance=instance)
    #     fairpyx.validate_allocation(instance, allocation, title=f"Seed {i}, OC_function")


    # s1 = {"c1": 40, "c2": 20, "c3": 10, "c4": 30}
    # s2 = {"c1": 6, "c2": 20, "c3": 70, "c4": 4}
    # s3 = {"c1": 9, "c2": 20, "c3": 21, "c4": 50}
    # s4 = {"c1": 25, "c2": 5, "c3": 15, "c4": 55}
    # s5 = {"c1": 5, "c2": 90, "c3": 3, "c4": 2}
    # instance = Instance(
    #     agent_capacities={"s1": 2, "s2": 2, "s3": 2, "s4": 2, "s5": 2},
    #     item_capacities={"c1": 3, "c2": 2, "c3": 2, "c4": 2},
    #     valuations={"s1": s1, "s2": s2, "s3": s3, "s4": s4, "s5": s5}
    # )
    # divide(OC_function, instance=instance)

    #s1 = {"c1": 400, "c2": 150, "c3": 230, "c4": 200, "c5": 20}
    #s2 = {"c1": 245, "c2": 252, "c3": 256, "c4": 246, "c5": 1}
    #s3 = {"c1": 243, "c2": 230, "c3": 240, "c4": 245, "c5": 42}
    #s4 = {"c1": 251, "c2": 235, "c3": 242, "c4": 201, "c5": 71}
    #instance = Instance(
    #    agent_capacities={"s1": 3, "s2": 3, "s3": 3, "s4": 3},
    #    item_capacities={"c1": 2, "c2": 3, "c3": 3, "c4": 2, "c5": 2},
    #    item_conflicts={"c1": ['c4'], "c4": ['c1']},
    #    valuations={"s1": s1, "s2": s2, "s3": s3, "s4": s4}
    #)

    #divide(OC_function, instance=instance)

    # np.random.seed(2)
    # instance = fairpyx.Instance.random_uniform(
    #     num_of_agents=70, num_of_items=10, normalized_sum_of_values=100,
    #     agent_capacity_bounds=[2, 6],
    #     item_capacity_bounds=[20, 40],
    #     item_base_value_bounds=[1, 1000],
    #     item_subjective_ratio_bounds=[0.5, 1.5]
    # )
    # allocation = divide(OC_function, instance=instance)

    # s1 = {"c1": 40, "c2": 20, "c3": 10, "c4": 30}
    # s2 = {"c1": 6, "c2": 20, "c3": 70, "c4": 4}
    # s3 = {"c1": 9, "c2": 20, "c3": 21, "c4": 50}
    # s4 = {"c1": 25, "c2": 5, "c3": 15, "c4": 55}
    # s5 = {"c1": 5, "c2": 90, "c3": 3, "c4": 2}
    # instance = fairpyx.Instance(
    #     agent_capacities={"s1": 2, "s2": 2, "s3": 2, "s4": 2, "s5": 2},
    #     item_capacities={"c1": 3, "c2": 2, "c3": 2, "c4": 2},
    #     valuations={"s1": s1, "s2": s2, "s3": s3, "s4": s4, "s5": s5}
    # )
    # allocation = divide(OC_function, instance=instance)

