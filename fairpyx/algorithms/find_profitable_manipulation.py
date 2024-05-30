"""
Implement a "Find a profitable manipulation for a student",

Programmers: Erga Bar-Ilan, Ofir Shitrit and Renana Turgeman.
Since: 2024-05
"""
import logging
from enum import Enum

import numpy as np

from fairpyx import Instance, AllocationBuilder
from fairpyx.adaptors import divide
from fairpyx.algorithms.ACEEI import find_ACEEI_with_EFTB


class criteria_for_profitable_manipulation(Enum):
    randomness = 0
    population = 1


logger = logging.getLogger(__name__)
NUMBER_OF_ITERATIONS = 10


# TODO: ask erel how to change the instance for the criteria population - how to change moti values to the correct


def random_initial_budgets(instance: Instance, beta: float):
    """
        Create random initial budgets for each student
       :param instance: a fair-course-allocation instance
    """
    return {agent: np.random.uniform(1 + (beta / 4), 1 + ((3 * beta) / 4)) for agent in instance.agents}


def create_misreports(original, neu):
    """
    Creates misreports for our student according to the neu parameter.
    :param original: the original student's utility
    :param neu: a local update coefficient

    >>> original = {"x": 1, "y": 2, "z": 4}
    >>> neu = 2
    >>> create_misreports(original, neu)
    [{'x': 0.5, 'y': 2, 'z': 4}, {'x': 2, 'y': 2, 'z': 4}, {'x': 1, 'y': 1.0, 'z': 4}, {'x': 1, 'y': 4, 'z': 4}, {'x': 1, 'y': 2, 'z': 2.0}, {'x': 1, 'y': 2, 'z': 8}]

    >>> original = {"x": 3, "y": 6, "z": 9}
    >>> neu = 3
    >>> create_misreports(original, neu)
    [{'x': 1.0, 'y': 6, 'z': 9}, {'x': 9, 'y': 6, 'z': 9}, {'x': 3, 'y': 2.0, 'z': 9}, {'x': 3, 'y': 18, 'z': 9}, {'x': 3, 'y': 6, 'z': 3.0}, {'x': 3, 'y': 6, 'z': 27}]
    """
    transformed_dicts = []

    for key in original:
        # Create a copy of the original dictionary for division
        divided_dict = original.copy()
        divided_dict[key] = original[key] / neu
        transformed_dicts.append(divided_dict)

        # Create a copy of the original dictionary for multiplication
        multiplied_dict = original.copy()
        multiplied_dict[key] = original[key] * neu
        transformed_dicts.append(multiplied_dict)

    return transformed_dicts


def get_random_utilities(instance: Instance):
    """
    Create random utilities for each student
    :param instance: a fair-course-allocation instance
    """
    return {course: np.random.uniform(1, 100) for course in instance.items}


def expected_value_of_specific_report_for_population(random_utilities: list[dict], random_budgets: list[dict], mechanism: callable,
                                      instance: Instance, student: str, delta: float, epsilon: float, t: Enum,
                                      report: dict):
    """
    Calculate the expected value of a student given a random utilities.

    :param random_utilities: a dictionary of random utilities
    :param random_budgets: a dictionary of random budgets
    :param mechanism: A randomized mechanism M for course-allocation
    :param instance: a fair-course-allocation instance
    :param student: The student who is being tested to see if he can manipulate
    :param delta: The step size
    :param epsilon: maximum budget perturbation
    :param t: type 𝑡 of the EF-TB constraint,
              0 for no EF-TB constraint,
              1 for EF-TB constraint,
              2 for contested EF-TB
    :param report: our student's utility
    """

    sum_utilities = 0
    for utility, iteration in zip(random_utilities, range(NUMBER_OF_ITERATIONS)):
        # todo: ask erel how to update the instance for the misreports
        # todo: change the agent to something else
        # todo: ask erel how to test it
        # print(f"random utilities:{random_utilities}")
        # print(f"random_utilities[iteration].items():{random_utilities[iteration].items()}")
        utilities = {agent: (report if agent == student else utility) for agent, utility in random_utilities[iteration].items()}
        # print(f"in E: utilities = {utilities}")
        # print("random_budgets[iteration]: %s", random_budgets[iteration], f"type {type(random_budgets[iteration])}")

        new_instance = Instance(valuations=utilities, agent_capacities=instance.agent_capacity, item_capacities=instance.item_capacity)
        allocation = divide(mechanism, instance=new_instance, initial_budgets=random_budgets[iteration], delta=delta,
                            epsilon=epsilon,
                            t=t)
        # logger.info("random_budgets[iteration]: %s", random_budgets[iteration], f"type {type(random_budgets[iteration])}")
        # print("random_budgets[iteration]: %s", random_budgets[iteration], f"type {type(random_budgets[iteration])}")
        # print(f"allocation: {allocation}")
        current_utility_found = instance.agent_bundle_value(student, allocation[student])
        sum_utilities += current_utility_found
    return sum_utilities / NUMBER_OF_ITERATIONS




def expected_value_of_specific_report_for_randomness(random_utilities: dict, random_budgets: list[dict], mechanism: callable,
                                                     instance: Instance, student: str, delta: float, epsilon: float, t: Enum,
                                                     report: dict):
    """
    Calculate the expected value of a student given a random utilities.

    :param random_utilities: a dictionary of random utilities
    :param random_budgets: a dictionary of random budgets
    :param mechanism: A randomized mechanism M for course-allocation
    :param instance: a fair-course-allocation instance
    :param student: The student who is being tested to see if he can manipulate
    :param delta: The step size
    :param epsilon: maximum budget perturbation
    :param t: type 𝑡 of the EF-TB constraint,
              0 for no EF-TB constraint,
              1 for EF-TB constraint,
              2 for contested EF-TB
    :param report: our student's utility
    """

    sum_utilities = 0
    for utility, iteration in zip(random_utilities, range(NUMBER_OF_ITERATIONS)):
        # todo: ask erel how to update the instance for the misreports
        # todo: change the agent to something else
        # todo: ask erel how to test it
        # print(f"random utilities:{random_utilities}")
        utilities = {agent: (report if agent == student else utility) for agent, utility in random_utilities.items()}
        # print(f"in E: utilities = {utilities}")
        # print("random_budgets[iteration]: %s", random_budgets[iteration], f"type {type(random_budgets[iteration])}")

        new_instance = Instance(valuations=utilities, agent_capacities=instance.agent_capacity, item_capacities=instance.item_capacity)
        allocation = divide(mechanism, instance=new_instance, initial_budgets=random_budgets[iteration], delta=delta,
                            epsilon=epsilon,
                            t=t)
        # logger.info("random_budgets[iteration]: %s", random_budgets[iteration], f"type {type(random_budgets[iteration])}")
        # print("random_budgets[iteration]: %s", random_budgets[iteration], f"type {type(random_budgets[iteration])}")
        # print(f"allocation: {allocation}")
        current_utility_found = instance.agent_bundle_value(student, allocation[student])
        sum_utilities += current_utility_found
    return sum_utilities / NUMBER_OF_ITERATIONS

def criteria_population(mechanism: callable, student: str, utility: dict, instance: Instance, delta: float,
                        epsilon: float, beta: float, t: Enum,  misreports: list):
    """
    Run algorithm 1 when initial budgets and other students utilities are Unknown.

    :param mechanism: A randomized mechanism M for course-allocation
    :param student: The student who is being tested to see if he can manipulate
    :param utility: The student's utility
    :param instance: a fair-course-allocation instance
    :param initial_budgets: Students' initial budgets
    :param delta: The step size
    :param epsilon: maximum budget perturbation
    :param t: type 𝑡 of the EF-TB constraint,
              0 for no EF-TB constraint,
              1 for EF-TB constraint,
              2 for contested EF-TB
    :param misreports: List of misreports for the students

    :return best manipulation that found for our student - the report that gives him the most benefit
    """
    # print("start population")
    best_manipulation_found = utility

    random_utilities = [{agent: get_random_utilities(instance) for agent in instance.agents} for _ in range(NUMBER_OF_ITERATIONS)]
    # random_budgets = [{agent: random_initial_budgets(instance, beta) for agent in instance.agents} for _ in range(NUMBER_OF_ITERATIONS)]
    random_budgets = [random_initial_budgets(instance, beta) for _ in range(NUMBER_OF_ITERATIONS)]

    # run for original utility
    max_expected_value = expected_value_of_specific_report_for_population(random_utilities, random_budgets, mechanism,
                                                           instance, student, delta, epsilon, t, utility)

    for misreport in misreports:
        current_expected_value = expected_value_of_specific_report_for_population(random_utilities, random_budgets, mechanism,
                                                                   instance, student, delta, epsilon, t, misreport)
        if current_expected_value > max_expected_value:
            max_expected_value = current_expected_value
            best_manipulation_found = misreport

    return best_manipulation_found


def criteria_randomness(mechanism: callable, student: str, utility: dict, instance: Instance, delta: float,
                        epsilon: float, t: Enum, initial_budgets: dict, misreports: list, beta: float):
    """
    Run algorithm 1 when initial budgets are Unknown.

    :param mechanism: A randomized mechanism M for course-allocation
    :param student: The student who is being tested to see if he can manipulate
    :param utility: The student's utility
    :param instance: a fair-course-allocation instance
    :param initial_budgets: Students' initial budgets
    :param delta: The step size
    :param epsilon: maximum budget perturbation
    :param t: type 𝑡 of the EF-TB constraint,
              0 for no EF-TB constraint,
              1 for EF-TB constraint,
              2 for contested EF-TB
    :param misreports: List of misreports for the students

    :return best manipulation that found for our student - the report that gives him the most benefit
    """
    #todo ask erel if to pass the initial budget
    # todo: ask erel how to update the instance
    #todo: ask erel how to get the _valuations


    # print("start raddomnes")
    best_manipulation_found = utility

    # random_budgets = [{agent: random_initial_budgets(instance, beta) for agent in instance.agents} for _ in range(NUMBER_OF_ITERATIONS)]
    random_budgets = [random_initial_budgets(instance, beta) for _ in range(NUMBER_OF_ITERATIONS)]
    # print(f"random_budgets: {random_budgets} ")

    # run for original utility
    max_expected_value = expected_value_of_specific_report_for_randomness(instance._valuations, random_budgets, mechanism,
                                                           instance, student, delta, epsilon, t, utility)


    for misreport in misreports:
        current_expected_value = expected_value_of_specific_report_for_randomness(instance._valuations, random_budgets, mechanism,
                                                                   instance, student, delta, epsilon, t, misreport)
        if current_expected_value > max_expected_value:
            max_expected_value = current_expected_value
            best_manipulation_found = misreport

    return best_manipulation_found


def find_profitable_manipulation(mechanism: callable, student: str, utility: dict,
                                 criteria: Enum, neu: float, instance: Instance, delta: float, epsilon: float, t: Enum,
                                 initial_budgets: dict,
                                 beta: float):
    """
   "Practical algorithms and experimentally validated incentives for equilibrium-based fair division (A-CEEI)"
    by ERIC BUDISH, RUIQUAN GAO, ABRAHAM OTHMAN, AVIAD RUBINSTEIN, QIANFAN ZHANG. (2023)
    ALGORITHM 2: Find a profitable manipulation for a student

    :param mechanism: A randomized mechanism M for course-allocation
    :param student: The student who is being tested to see if he can manipulate
    :param utility: The student's utility
    :param criteria: The type of criteria for profitable manipulation
                                                 0 for resampled randomness
                                                 1 for population
    :param neu: a local update coefficient neu
    :param alloc: a fair-course-allocation instance
    :param initial_budgets: Students' initial budgets
    :param delta: The step size
    :param epsilon: maximum budget perturbation
    :param t: type 𝑡 of the EF-TB constraint,
              0 for no EF-TB constraint,
              1 for EF-TB constraint,
              2 for contested EF-TB
    :param beta: a parameter that determines the distribution of the initial budgets

    return: The profitable manipulation

    >>> from fairpyx.algorithms.ACEEI import find_ACEEI_with_EFTB
    >>> from fairpyx.algorithms import ACEEI, tabu_search
    >>> logger.addHandler(logging.StreamHandler())
    >>> logger.setLevel(logging.INFO)

    Example run 1
    >>> mechanism = find_ACEEI_with_EFTB
    >>> student = "moti"
    >>> utility = {"x":1, "y":2, "z":4}
    >>> criteria = criteria_for_profitable_manipulation.randomness
    >>> neu = 2
    >>> instance = Instance(
    ...     valuations={"avi":{"x":3, "y":5, "z":1}, "beni":{"x":2, "y":3, "z":1}, "moti": {"x":1, "y":2, "z":4}},
    ...     agent_capacities=2,
    ...     item_capacities={"x":1, "y":2, "z":3})
    >>> beta = 2
    >>> initial_budgets = random_initial_budgets(instance, beta)
    >>> delta = 0.5
    >>> epsilon = 0.5
    >>> t = ACEEI.EFTBStatus.NO_EF_TB
    >>> find_profitable_manipulation(mechanism, student, utility, criteria, neu, instance, delta, epsilon, t, initial_budgets, beta)
    {'x': 1, 'y': 2, 'z': 4}

    Example run 2
    >>> mechanism = find_ACEEI_with_EFTB
    >>> student = "moti"
    >>> utility = {"x":1, "y":2, "z":4}
    >>> criteria = criteria_for_profitable_manipulation.randomness
    >>> neu = 2
    >>> instance = Instance(
    ...     valuations={"avi":{"x":3, "y":5, "z":1}, "beni":{"x":2, "y":3, "z":1}, "moti": {"x":1, "y":2, "z":4}},
    ...     agent_capacities=2,
    ...     item_capacities={"x":1, "y":2, "z":3})
    >>> beta = 2
    >>> initial_budgets = random_initial_budgets(instance, beta)
    >>> delta = 0.5
    >>> epsilon = 0.5
    >>> t = ACEEI.EFTBStatus.EF_TB
    >>> find_profitable_manipulation(mechanism, student, utility, criteria, neu, instance, delta, epsilon, t, initial_budgets, beta)
    {'x': 1, 'y': 2, 'z': 4}


    Example run 4
    >>> mechanism = find_ACEEI_with_EFTB
    >>> student = "moti"
    >>> utility = {"x":6, "y":2}
    >>> criteria = criteria_for_profitable_manipulation.randomness
    >>> neu = 2
    >>> instance = Instance(
    ...     valuations={"avi":{"x":5, "y":3}, "moti": {"x":6, "y":2}},
    ...     agent_capacities=2,
    ...     item_capacities={"x":1, "y":2})
    >>> beta = 2
    >>> initial_budgets = random_initial_budgets(instance, beta)
    >>> delta = 0.5
    >>> epsilon = 0.5
    >>> t = ACEEI.EFTBStatus.NO_EF_TB
    >>> find_profitable_manipulation(mechanism, student, utility, criteria, neu, instance, delta, epsilon, t, initial_budgets, beta)
    {'x': 6, 'y': 2}

    # Example run 5
    >>> mechanism = find_ACEEI_with_EFTB
    >>> student = "moti"
    >>> utility = {"x":1, "y":2, "z":5}
    >>> criteria = criteria_for_profitable_manipulation.population
    >>> neu = 2
    >>> instance = Instance(valuations={"avi":{"x":5, "y":4, "z":1}, "beni":{"x":4, "y":6, "z":3}, "moti":{"x":1, "y":2, "z":5}},
    ...            agent_capacities=2,
    ...            item_capacities={"x":1, "y":2, "z":3})
    >>> beta = 2
    >>> initial_budgets = random_initial_budgets(instance, beta)
    >>> delta = 0.5
    >>> epsilon = 0.5
    >>> t = ACEEI.EFTBStatus.NO_EF_TB
    >>> find_profitable_manipulation(mechanism, student, utility, criteria, neu, instance, delta, epsilon, t, initial_budgets, beta)
    {'x': 1, 'y': 2, 'z': 5}

   """
    # print("start algo2")
    # (1) Let 𝑣0 ←𝑢( or the best manipulation found in previous iterations with different 𝜂).
    current_best_manipulation = {}

    initial_budgets = random_initial_budgets(instance, beta)

    while True:
        # (2) Try to  increase or decrease the weight 𝑤𝑗 for each course 𝑗 in 𝑣0 to obtain new misreports
        #      𝑉 = {𝑣𝑗,±1}𝑗∈[𝑚]}
        misreports = create_misreports(current_best_manipulation, neu)
        # print("create misreports")

        # (3) Let 𝑣∗ = argmax𝑣∈𝑉∪{𝑣0} E𝒓∼R[𝑢𝑖(𝑴𝑖([𝑣𝑗, 𝒖−𝑖], 𝒄, 𝒓))] resampled randomness,
        #              argmax𝑣∈𝑉∪{𝑣0} E𝒖−𝑖∼U−𝑖, 𝒓∼R[𝑢𝑖(𝑴𝑖([𝑣𝑗, 𝒖−𝑖], 𝒄, 𝒓))] resampled population.

        if criteria == criteria_for_profitable_manipulation.population:
            current_best_manipulation = criteria_population(mechanism, student, utility, instance, delta, epsilon, beta,
                                                            t,misreports)
        else:  # criteria == criteria_for_profitable_manipulation.randomness
            current_best_manipulation = criteria_randomness(mechanism, student, utility, instance, delta, epsilon, t,
                                                            initial_budgets,
                                                            misreports, beta)
        if current_best_manipulation == utility:
            break
        else:
            utility = current_best_manipulation

    # (4) If 𝑣∗ = 𝑣0, terminate with 𝑣0 as the best manipulation found when 𝑣0 ≠ 𝑢, otherwise return failed.
    return current_best_manipulation

if __name__ == '__main__':
    from fairpyx.algorithms import ACEEI

    mechanism = find_ACEEI_with_EFTB
    student = "moti"
    utility = {"x": 1, "y": 2, "z": 4}
    criteria = criteria_for_profitable_manipulation.randomness
    neu = 2
    instance = Instance(valuations = {"avi": {"x": 3, "y": 5, "z": 1}, "beni": {"x": 2, "y": 3, "z": 1}, "moti": {"x": 1, "y": 2, "z": 4}},
    agent_capacities = 2,
    item_capacities = {"x": 1, "y": 2, "z": 3})
    beta = 2
    initial_budgets = random_initial_budgets(instance, beta)
    delta = 0.5
    epsilon = 0.5
    t = ACEEI.EFTBStatus.NO_EF_TB
    find_profitable_manipulation(mechanism, student, utility, criteria, neu, instance, delta, epsilon, t,
                                      initial_budgets, beta)

    #
    # mechanism = find_ACEEI_with_EFTB
    # student = "moti"
    # utility = {"x":1, "y":2, "z":5}
    # criteria = criteria_for_profitable_manipulation.population
    # neu = 2
    # instance = Instance(valuations={"avi":{"x":5, "y":4, "z":1}, "beni":{"x":4, "y":6, "z":3}, "moti":{"x":1, "y":2, "z":5}},
    #                     agent_capacities=2,
    #                     item_capacities={"x":1, "y":2, "z":3})
    # beta = 2
    # initial_budgets = random_initial_budgets(instance, beta)
    # delta = 0.5
    # epsilon = 0.5
    # t = ACEEI.EFTBStatus.NO_EF_TB
    # find_profitable_manipulation(mechanism, student, utility, criteria, neu, instance, delta, epsilon, t, initial_budgets, beta)
