"""
Implement "Tabu search" course allocation,

Programmers: Erga Bar-Ilan, Ofir Shitrit and Renana Turgeman.
Since: 2024-01
"""
import logging
import random
from itertools import combinations

import numpy as np

from fairpyx import Instance, AllocationBuilder

logger = logging.getLogger(__name__)


def excess_demand(instance: Instance, allocation: dict):
    """
    Calculate for every course its excess demand
    𝑧𝑗 (𝒖,𝒄, 𝒑, 𝒃) = ∑︁ 𝑎𝑖𝑗 (𝒖, 𝒑, 𝒃) − 𝑐𝑗
                  𝑖=1 to n

    :param instance: fair-course-allocation instance
    :param allocation: a dictionary that maps each student to his bundle

    :return: a dictionary that maps each course to its excess demand

    >>> instance = Instance(
    ... valuations={"ami":{"x":3, "y":4, "z":2}, "tami":{"x":4, "y":3, "z":2}},
    ... agent_capacities=2,
    ... item_capacities={"x":2, "y":1, "z":3})
    >>> allocation = {"ami":('x','y'), "tami":('x','y')}
    >>> excess_demand(instance, allocation)
    {'x': 0, 'y': 1, 'z': -3}
    """
    z = {}  # Initialize z as a dictionary
    for course in instance.items:
        sum_allocation = 0
        for student, bundle in allocation.items():
            if course in bundle:
                sum_allocation += 1
        z[course] = sum_allocation - instance.item_capacity(course)
    return z


def clipped_excess_demand(instance: Instance, prices: dict, allocation: dict):
    """
       Calculate for every course its clipped excess demand
       𝑧˜𝑗 (𝒖,𝒄, 𝒑, 𝒃) =  𝑧𝑗 (𝒖,𝒄, 𝒑, 𝒃) if 𝑝𝑗 > 0,
                         max{0, 𝑧𝑗 (𝒖,𝒄, 𝒑, 𝒃)} if 𝑝𝑗 = 0


       :param instance: fair-course-allocation instance
       :param allocation: a dictionary that maps each student to his bundle

       :return: a dictionary that maps each course to its clipped excess demand

       >>> instance = Instance(
       ... valuations={"ami":{"x":3, "y":4, "z":2}, "tami":{"x":4, "y":3, "z":2}},
       ... agent_capacities=2,
       ... item_capacities={"x":2, "y":1, "z":3})
       >>> allocation = {"ami":('x','y'), "tami":('x','y')}
       >>> prices = {"x":2, "y":2, "z":0}
       >>> clipped_excess_demand(instance ,prices, allocation)
       {'x': 0, 'y': 1, 'z': 0}
    """
    z = excess_demand(instance, allocation)
    clipped_z = {course: max(0, z[course]) if prices[course] == 0 else z[course] for course in z}
    return clipped_z


def student_best_bundle(prices: dict, instance: Instance, initial_budgets: dict):
    """
    Return a dict that says for each student what is the bundle with the maximum utility that a student can take

    :param prices: dictionary with courses prices
    :param instance: fair-course-allocation instance
    :param initial_budgets: students' initial budgets

    :return: a dictionary that maps each student to its best bundle.

     Example run 1 iteration 1
    >>> instance = Instance(
    ...     valuations={"Alice":{"x":3, "y":4, "z":2}, "Bob":{"x":4, "y":3, "z":2}, "Eve":{"x":2, "y":4, "z":3}},
    ...     agent_capacities=2,
    ...     item_capacities={"x":2, "y":1, "z":3})
    >>> initial_budgets = {"Alice": 5, "Bob": 4, "Eve": 3}
    >>> prices = {"x": 1, "y": 2, "z": 1}
    >>> student_best_bundle(prices, instance, initial_budgets)
    {'Alice': ('x', 'y'), 'Bob': ('x', 'y'), 'Eve': ('y', 'z')}

     Example run 2 iteration 1
    >>> instance = Instance(
    ...     valuations={"Alice":{"x":5, "y":4, "z":3, "w":2}, "Bob":{"x":5, "y":2, "z":4, "w":3}},
    ...     agent_capacities=3,
    ...     item_capacities={"x":1, "y":2, "z":1, "w":2})
    >>> initial_budgets = {"Alice": 8, "Bob": 6}
    >>> prices = {"x": 1, "y": 2, "z": 3, "w":4}
    >>> student_best_bundle(prices, instance, initial_budgets)
    {'Alice': ('x', 'y', 'z'), 'Bob': ('x', 'y', 'z')}


    Example run 3 iteration 1
    >>> instance = Instance(
    ...     valuations={"Alice":{"x":3, "y":3, "z":3, "w":3}, "Bob":{"x":3, "y":3, "z":3, "w":3}, "Eve":{"x":4, "y":4, "z":4, "w":4}},
    ...     agent_capacities=2,
    ...     item_capacities={"x":1, "y":2, "z":2, "w":1})
    >>> initial_budgets = {"Alice": 4, "Bob": 5, "Eve": 2}
    >>> prices = {"x": 1, "y": 1, "z": 1, "w":1}
    >>> student_best_bundle(prices, instance, initial_budgets)
    {'Alice': ('x', 'y'), 'Bob': ('x', 'y'), 'Eve': ('x', 'y')}

    """
    best_bundle = {student: None for student in instance.agents}
    logger.info("START combinations")

    for student in instance.agents:

        # Creating a list of combinations of courses up to the size of the student's capacity
        combinations_courses_list = []
        capacity = instance.agent_capacity(student)
        for r in range(1, capacity + 1):
            combinations_courses_list.extend(combinations(instance.items, r))
        logger.info(f"FINISH combinations for {student}")

        # Define a lambda function that calculates the valuation of a combination
        valuation_function = lambda combination: instance.agent_bundle_value(student, combination)

        # Sort the combinations_set based on their valuations in descending order
        combinations_courses_sorted = sorted(combinations_courses_list, key=valuation_function, reverse=True)

        for combination in combinations_courses_sorted:
            price_combination = sum(prices[course] for course in combination)
            if price_combination <= initial_budgets[student]:
                best_bundle[student] = combination
                break

    return best_bundle


def find_all_equivalent_prices(instance: Instance, initial_budgets: dict, allocation: dict):
    """
    find all equivalent prices- list of all equivalent prices of 𝒑

    :param instance: fair-course-allocation
    :param initial_budgets: students' initial budgets
    :param allocation: a dictionary that maps each student to his bundle

    Example run 1
    >>> instance = Instance(valuations={"A":{"x":3, "y":4, "z":2},
    ...    "B":{"x":4, "y":3, "z":2}, "C":{"x":2, "y":4, "z":3}},
    ...     agent_capacities=2,
    ...     item_capacities={"x":2, "y":1, "z":3})
    >>> initial_budgets = {"A": 5, "B":4, "C":3}
    >>> allocation = {"A": {'x', 'y'}, "B":{'x', 'y'}, "C":{'y', 'z'}}
    >>> equivalent_prices = find_all_equivalent_prices(instance, initial_budgets, allocation)
    >>> p = {"x":1, "y":2, "z":1}
    >>> any([f(p) for f in equivalent_prices])
    True
    >>> p = {"x":5, "y":5, "z":5}
    >>> any([f(p) for f in equivalent_prices])
    False

    # [(['x', 'y'], '<=', 5), (['x', 'y'], '<=', 4), (['y', 'z'], '<=', 3)]

    Example run 1
    >>> instance = Instance(valuations={"A":{"x":3, "y":4, "z":2},
    ...    "B":{"x":4, "y":3, "z":2}, "C":{"x":2, "y":4, "z":3}},
    ...     agent_capacities=2,
    ...     item_capacities={"x":2, "y":1, "z":3})
    >>> initial_budgets = {"A": 5, "B":4, "C":3}
    >>> allocation = {"A": {'x', 'y'}, "B":{'x', 'z'}, "C":{'x', 'z'}}
    >>> equivalent_prices = find_all_equivalent_prices(instance, initial_budgets, allocation)
    >>> p = {"x":0, "y":0, "z":0}
    >>> any([f(p) for f in equivalent_prices])
    True
    >>> p = {"x":1, "y":5, "z":1}
    >>> any([f(p) for f in equivalent_prices])
    True
    >>> p = {"x":1, "y":3, "z":1}
    >>> any([f(p) for f in equivalent_prices])
    True

    # [(['x', 'y'], '<=', 5), (['x', 'z'], '<=', 4), (['x', 'z'], '<=', 3), (['x', 'y'], '>=', 4), (['x', 'y'], '>=', 3), (['y', 'z'], '>=', 3)]


    Example run 2
    >>> instance = Instance(valuations={"A":{"x":5, "y":4, "z":3, "w":2},"B":{"x":5, "y":2, "z":4, "w":3}},
    ...     agent_capacities=3,
    ...     item_capacities={"x":1, "y":2, "z":1, "w":2})
    >>> initial_budgets = {"A": 8, "B":6}
    >>> allocation = {"A": {'x', 'y','z'}, "B":{'x','y' ,'z'}}
    >>> equivalent_prices = find_all_equivalent_prices(instance, initial_budgets, allocation)
    >>> p = {"x":1, "y":3, "z":2, "w":4}
    >>> any([f(p) for f in equivalent_prices])
    True
    >>> p = {"x":2, "y":2, "z":4, "w":2}
    >>> any([f(p) for f in equivalent_prices])
    True
    >>> p = {"x":2, "y":2, "z":4, "w":2}
    >>> any([f(p) for f in equivalent_prices])
    False

    # [(['x', 'y', 'z'], '<=', 8), (['x', 'y', 'z'], '<=', 6), (['w', 'x', 'z'], '>=', 6)]


    """
    # TODO: ask erel about that the alloc get good answer but in diffrent order
    equivalent_prices = []
    # The constraints that the bundles they get in allocation meet their budgets
    for agent in allocation.keys():
        sorted_allocation = sorted(allocation[agent])  # Sort the allocation for the agent
        equivalent_prices.append(lambda p: sum(p[key] for key in sorted_allocation) <= initial_budgets[agent])

    # Constraints that will ensure that this is the allocation that will be accepted
    for student in instance.agents:
        # Creating a list of combinations of courses up to the size of the student's capacity
        combinations_courses_list = []
        capacity = instance.agent_capacity(student)
        for r in range(1, capacity + 1):
            combinations_courses_list.extend(combinations(instance.items, r))

        utility = instance.agent_bundle_value(student, allocation[student])
        for combination in combinations_courses_list:
            current_utility = instance.agent_bundle_value(student, combination)
            sorted_combination = sorted(combination)
            if sorted_combination != sorted(allocation[student]) and current_utility >= utility:
                equivalent_prices.append(
                    lambda p: sum(p[key] for key in sorted_combination) >= initial_budgets[student])

    # print(equivalent_prices)
    return equivalent_prices


def find_gradient_neighbors(neighbors: list, history: list, prices: dict, delta: float, excess_demand_vector: dict):
    # TODO ask erel about delta
    """
    Add the gradient neighbors to the neighbors list
    N_gradient(𝒑, Δ) = {𝒑 + 𝛿 · 𝒛(𝒖,𝒄, 𝒑, 𝒃) : 𝛿 ∈ Δ}

    :param neighbors: list of Gradient neighbors and Individual price adjustment neighbors.
    :param history: all equivalent prices of 𝒑
    :param prices: dictionary with courses prices
    :param delta:
    :param excess_demand_vector: excess demand of the courses
    :return: None

    Example run 1 iteration 1
    >>> neighbors = []
    >>> history = []
    >>> prices = {"x": 1, "y": 2, "z": 1}
    >>> delta = 1
    >>> excess_demand_vector = {"x":0,"y":2,"z":-2}
    >>> find_gradient_neighbors(neighbors,history,prices,delta,excess_demand_vector)
    {'x': 1, 'y': 4, 'z': 0}


     Example run 1 iteration 2
    >>> neighbors = []
    >>> history = [
    ...    {'x': 1, 'y': 2, 'z': 1}, {'x': 0, 'y': 0, 'z': 0}, {'x': 1, 'y': 0, 'z': 0},
    ...    {'x': 0, 'y': 1, 'z': 0}, {'x': 0, 'y': 0, 'z': 1}, {'x': 1, 'y': 1, 'z': 0},
    ...    {'x': 1, 'y': 0, 'z': 1}, {'x': 0, 'y': 1, 'z': 1}, {'x': 1, 'y': 1, 'z': 1},
    ...    {'x': 0, 'y': 1, 'z': 2}, {'x': 0, 'y': 2, 'z': 1}, {'x': 1, 'y': 0, 'z': 2},
    ...    {'x': 1, 'y': 2, 'z': 0}, {'x': 2, 'y': 0, 'z': 1}, {'x': 2, 'y': 1, 'z': 0},
    ...    {'x': 2, 'y': 2, 'z': 0}, {'x': 2, 'y': 2, 'z': 1}, {'x': 1, 'y': 1, 'z': 2},
    ...    {'x': 2, 'y': 1, 'z': 1}, {'x': 3, 'y': 0, 'z': 0}, {'x': 3, 'y': 1, 'z': 0},
    ...    {'x': 3, 'y': 0, 'z': 1}, {'x': 3, 'y': 1, 'z': 1}, {'x': 0, 'y': 3, 'z': 0},
    ...    {'x': 1, 'y': 3, 'z': 0}, {'x': 0, 'y': 0, 'z': 3}, {'x': 1, 'y': 0, 'z': 3},
    ...   {'x': 2, 'y': 0, 'z': 3}, {'x': 3, 'y': 0, 'z': 3}, {'x': 4, 'y': 0, 'z': 3},
    ...   {'x': 1, 'y': 4, 'z': 0}, {'x': 2, 'y': 3, 'z': 1}, {'x': 0, 'y': 5, 'z': 0}]
    >>> prices = {"x": 1, "y": 4, "z": 0}
    >>> delta = 1
    >>> excess_demand_vector = {"x":1,"y":0,"z":0}
    >>> find_gradient_neighbors(neighbors,history,prices,delta,excess_demand_vector)
    {'x': 2, 'y': 4, 'z': 0}
    """

    updated_prices = {}
    for item, price in prices.items():
        updated_prices[item] = max(0, price + delta * excess_demand_vector.get(item, 0))

    # if updated_prices not in history:
    neighbors.append(updated_prices)

    return updated_prices


def differ_in_one_value(original_allocation: dict, new_allocation: dict, course: str) -> bool:
    """
    Check if two dictionaries differ with each other in exactly one value.

    :param original_allocation: First dictionary
    :param new_allocation: Second dictionary
    :return: True if the dictionaries differ in exactly one value, False otherwise

    >>> allocation1 = {"ami":('x','y'),"tami":('x','z'),"tzumi":('x','z')}
    >>> allocation2 = {"ami":('x','y'),"tami":('x','z'),"tzumi":('x','t')}
    >>> course ="z"
    >>> differ_in_one_value(allocation1, allocation2, course)
    True

    >>> allocation1 = {"ami":('x','y'),"tami":('x','z'),"tzumi":('x','z')}
    >>> allocation2 = {"ami":('x','y'),"tami":('h','z'),"tzumi":('x','t')}
    >>> course = "x"
    >>> differ_in_one_value(allocation1, allocation2, course)
    False

    >>> allocation1 = {"ami":('x','y'),"tami":('x','z'),"tzumi":('x','z')}
    >>> allocation2 = {"ami":('x','y'),"tami":('x','z'),"tzumi":('x','z')}
    >>> course = "z"
    >>> differ_in_one_value(allocation1, allocation2, course)
    False

    >>> allocation1 = {"ami":('x','y'),"tami":('x','z'),"tzumi":('x','z')}
    >>> allocation2 = {"ami":('y','z'),"tami":('x','z'),"tzumi":('x','z')}
    >>> course = "x"
    >>> differ_in_one_value(allocation1, allocation2 , course)
    True
    """
    # Count the number of differing values
    diff_count = 0
    diff_course = None
    for key in original_allocation:
        if key in new_allocation and original_allocation[key] != new_allocation[key]:
            diff_course = key
            diff_count += 1
            # If more than one value differs, return False immediately
            if diff_count > 1:
                return False
    # Return True if exactly one value differs
    return diff_count == 1 and course in original_allocation[diff_course] and course not in new_allocation[diff_course]


def find_individual_price_adjustment_neighbors(instance: Instance, neighbors: list, history: list, prices: dict,
                                               excess_demand_vector: dict, initial_budgets: dict, allocation: dict):
    """
    Add the individual price adjustment neighbors to the neighbors list

    :param instance: fair-course-allocation
    :param neighbors: list of Gradient neighbors and Individual price adjustment neighbors.
    :param history: all equivalent prices of 𝒑
    :param prices: dictionary with courses prices
    :param excess_demand_vector: excess demand of the courses
    :param initial_budgets: students' initial budgets
    :param allocation: a dictionary that maps each student to his bundle
    :return: None

    Example run 1 iteration 1
    >>> instance = Instance(
    ... valuations={"ami":{"x":3, "y":4, "z":2}, "tami":{"x":4, "y":3, "z":2}, "tzumi":{"x":2, "y":4, "z":3}},
    ... agent_capacities=2,
    ... item_capacities={"x":2, "y":1, "z":3})
    >>> neighbors = []
    >>> history = [lambda p: p['x']+p['y']<=5, lambda p: p['x']+p['y']<=4, lambda p: p['y']+p['z']<=3]
    >>> prices = {"x": 1, "y": 2, "z": 1}
    >>> excess_demand_vector = {"x":0,"y":2,"z":-2}
    >>> initial_budgets = {"ami":5,"tami":4,"tzumi":3}
    >>> allocation = {"ami":('x','y'),"tami":('x','y'),"tzumi":('y','z')}
    >>> find_individual_price_adjustment_neighbors(instance,neighbors, history, prices, excess_demand_vector, initial_budgets, allocation)
    [{'x': 1, 'y': 3, 'z': 1}]


     Example run 1 iteration 2
    >>> instance = Instance(
    ... valuations={"ami":{"x":3, "y":4, "z":2}, "tami":{"x":4, "y":3, "z":2}, "tzumi":{"x":2, "y":4, "z":3}},
    ... agent_capacities=2,
    ... item_capacities={"x":2, "y":1, "z":3})
    >>> neighbors = []
    >>> history = [lambda p: p['x']+p['y']<=5, lambda p: p['x']+p['y']<=4, lambda p: p['y']+p['z']<=3,
    ...           lambda p: p['x']+p['z']<=4, lambda p: p['x']+p['z']<=3, lambda p: p['y']+p['z']>=3, lambda p: p['x']+p['y']>=4]
    >>> prices = {"x": 1, "y": 4, "z": 0}
    >>> excess_demand_vector = {"x":1,"y":0,"z":0}
    >>> initial_budgets = {"ami":5,"tami":4,"tzumi":3}
    >>> allocation = {"ami":('x','y'),"tami":('x','z'),"tzumi":('x','z')}
    >>> find_individual_price_adjustment_neighbors(instance,neighbors, history, prices, excess_demand_vector, initial_budgets, allocation)
    [{'x': 2, 'y': 4, 'z': 0}, {'x': 3, 'y': 4, 'z': 0}]
    """

    for course, excess_demand in excess_demand_vector.items():
        if excess_demand == 0:
            continue
        updated_prices = prices.copy()
        if excess_demand > 0:
            for _ in range(35):
                updated_prices[course] += 1
                # if updated_prices in history:
                if any([f(updated_prices) for f in history]):
                    continue
                # get the new demand of the course
                new_allocation = student_best_bundle(updated_prices, instance, initial_budgets)
                if (differ_in_one_value(new_allocation, allocation, course) and updated_prices not in neighbors):
                    logger.info(f"Found new allocation for {allocation}")
                    neighbors.append(updated_prices.copy())


        elif excess_demand < 0:
            updated_prices[course] = 0
            # if updated_prices not in history and updated_prices not in neighbors:
            if not any([f(updated_prices) for f in history]) and updated_prices not in neighbors:
                neighbors.append(updated_prices)

    return neighbors


def find_all_neighbors(instance: Instance, neighbors: list, history: list, prices: dict, delta: float,
                       excess_demand_vector: dict, initial_budgets: dict, allocation: dict):
    # TODO: ask erel about delta
    """
    Update neighbors N (𝒑) - list of Gradient neighbors and Individual price adjustment neighbors.

    :param instance: fair-course-allocation
    :param neighbors: list of Gradient neighbors and Individual price adjustment neighbors.
    :param history: all equivalent prices of 𝒑
    :param prices: dictionary with courses prices
    :param delta:
    """

    find_gradient_neighbors(neighbors, history, prices, delta, excess_demand_vector)
    find_individual_price_adjustment_neighbors(instance, neighbors, history, prices,
                                               excess_demand_vector, initial_budgets, allocation)


def find_min_error_prices(instance: Instance, neighbors: list, initial_budgets: dict):
    """
    Return the update prices that minimize the market clearing error.

    :param instance: fair-course-allocation
    :param prices: dictionary with course prices
    :param neighbors: list of Gradient neighbors and Individual price adjustment neighbors.
    :param initial_budgets: students' initial budgets

    :return: update prices

    Example run 1 iteration 1
    >>> instance = Instance(
    ... valuations={"ami":{"x":3, "y":4, "z":2}, "tami":{"x":4, "y":3, "z":2}, "tzumi":{"x":2, "y":4, "z":3}},
    ... agent_capacities=2,
    ... item_capacities={"x":2, "y":1, "z":3})
    >>> neighbors = [{"x":1, "y":4, "z":0}, {"x":1, "y":3, "z":1}]
    >>> initial_budgets={"ami":5, "tami":4, "tzumi":3}
    >>> find_min_error_prices(instance, neighbors, initial_budgets)
    {'x': 1, 'y': 4, 'z': 0}

     Example run 1 iteration 2
    >>> instance = Instance(
    ... valuations={"ami":{"x":3, "y":4, "z":2}, "tami":{"x":4, "y":3, "z":2}, "tzumi":{"x":2, "y":4, "z":3}},
    ... agent_capacities=2,
    ... item_capacities={"x":2, "y":1, "z":3})
    >>> neighbors = [{"x":2, "y":4, "z":0}, {"x":3, "y":4, "z":0}]
    >>> initial_budgets={"ami":5, "tami":4, "tzumi":3}
    >>> find_min_error_prices(instance, neighbors, initial_budgets)
    {'x': 2, 'y': 4, 'z': 0}

    """
    min_error = float('inf')
    prices_vector = None
    for neighbor in neighbors:
        allocation = student_best_bundle(neighbor, instance, initial_budgets)
        error = clipped_excess_demand(instance, neighbor, allocation)
        norma2 = np.linalg.norm(np.array(list(error.values())))

        if norma2 < min_error:
            min_error = norma2
            prices_vector = neighbor

    return prices_vector


def tabu_search(instance: Instance, initial_budgets: dict, beta: float):
    """
   "Practical algorithms and experimentally validated incentives for equilibrium-based fair division (A-CEEI)"
    by ERIC BUDISH, RUIQUAN GAO, ABRAHAM OTHMAN, AVIAD RUBINSTEIN, QIANFAN ZHANG. (2023)
    ALGORITHM 3: Tabu search

   :param instance: a fair-course-allocation instance
   :param initial_budgets: Students' initial budgets, b_0∈[1,1+β]^n
   :param beta: creates the range of initial_budgets

   :return final courses prices, final distribution

    >>> from fairpyx.adaptors import divide
    >>> from fairpyx.utils.test_utils import stringify
    >>> from fairpyx import Instance

    >>> instance = Instance(
    ... valuations={"ami":{"x":3, "y":4, "z":2}, "tami":{"x":4, "y":3, "z":2}, "tzumi":{"x":2, "y":4, "z":3}},
    ... agent_capacities=2,
    ... item_capacities={"x":2, "y":1, "z":3})
    >>> initial_budgets={"ami":5, "tami":4, "tzumi":3}
    >>> beta = 4
    >>> stringify(divide(tabu_search, instance=instance, initial_budgets=initial_budgets,beta=beta))
    "{ami:['y','z'], tami:['x', 'z'], tzumi:['x', 'z'] }"

    >>> instance = Instance(
    ... valuations={"ami":{"x":5, "y":4, "z":3, "w":2}, "tami":{"x":5, "y":2, "z":4, "w":3}},
    ... agent_capacities=3,
    ... item_capacities={"x":1, "y":2, "z":1, "w":2})
    >>> initial_budgets={"ami":8, "tami":6}
    >>> beta = 9
    >>> stringify(divide(tabu_search, instance=instance, initial_budgets=initial_budgets,beta=beta))
    "{ami:['x','y','z'], tami:['x', 'z', 'w']}"

    >>> instance = Instance(
    ... valuations={"ami":{"x":3, "y":3, "z":3}, "tami":{"x":3, "y":3, "z":3}, "tzumi":{"x":4, "y":4, "z":4}},
    ... agent_capacities=2,
    ... item_capacities={"x":1, "y":2, "z":2, "w":1})
    >>> initial_budgets={"ami":4, "tami":5, "tzumi":2}
    >>> beta = 5
    >>> stringify(divide(tabu_search, instance=instance, initial_budgets=initial_budgets,beta=beta))
    "{ami:['y','z'], tami:['x', 'w'], tzumi:['y', 'z'] }"

    >>> instance = Instance(
    ... valuations={"ami":{"x":4, "y":3, "z":2}, "tami":{"x":5, "y":1, "z":2}},
    ... agent_capacities=2,
    ... item_capacities={"x":1, "y":2, "z":3})
    >>> initial_budgets={"ami":6, "tami":4}
    >>> beta = 6
    >>> stringify(divide(tabu_search, instance=instance, initial_budgets=initial_budgets,beta=beta))
    "{ami:['x','y'], tami:['y', 'z']}"

    >>> instance = Instance(
    ... valuations={"ami":{"x":4, "y":3, "z":2}, "tami":{"x":5, "y":1, "z":2}},
    ... agent_capacities=2,
    ... item_capacities={"x":1, "y":1, "z":1})
    >>> initial_budgets={"ami":5, "tami":3}
    >>> beta = 6
    >>> stringify(divide(tabu_search, instance=instance, initial_budgets=initial_budgets,beta=beta))
    "{ami:['y','z'], tami:['x']}"
    """
    # 1) Let 𝒑 ← uniform(1, 1 + 𝛽)^𝑚, H ← ∅.
    prices = {course: random.uniform(1, 1 + beta) for course in instance.items}
    history = {}

    # 2)  If ∥𝒛(𝒖,𝒄, 𝒑, 𝒃0)∥2 = 0, terminate with 𝒑∗ = 𝒑.
    norma2 = 1
    while norma2:
        neighbors = []  # resets on every iteration
        allocation = student_best_bundle(prices, instance, initial_budgets)
        excess_demand_vector = clipped_excess_demand(instance, prices, allocation)
        values = np.array(list(excess_demand_vector.values()))
        norma2 = np.linalg.norm(values)

        # If ∥𝒛˜(𝒖,𝒄, 𝒑, 𝒃) ∥2 = 0, terminate with 𝒑* = 𝒑
        if np.allclose(norma2, 0):
            break

        # 3) Otherwise,
        # • include all equivalent prices of 𝒑 into the history: H ← H + {𝒑′ : 𝒑′ ∼𝑝 𝒑},
        equivalent_prices = find_all_equivalent_prices(instance, initial_budgets, allocation)
        history.add(equivalent_prices)
        delta = 1  # TODO- ask erel how to get delta
        find_all_neighbors(instance, neighbors, history, prices, delta, excess_demand_vector, initial_budgets,
                           allocation)

        # • update 𝒑 ← arg min𝒑′∈N (𝒑)−H ∥𝒛(𝒖,𝒄, 𝒑', 𝒃0)∥2, and then
        find_min_error_prices(instance, neighbors, initial_budgets)

    # print the final price (p* = prices) for each course
    logger.info(f"\nfinal prices p* = {prices}")
    return allocation


if __name__ == "__main__":
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)

    # import doctest
    #
    # doctest.testmod()
    #
    # instance = Instance(
    #     valuations={"ami": {"x": 3, "y": 4, "z": 2}, "tami": {"x": 4, "y": 3, "z": 2}},
    #     agent_capacities=2,
    #     item_capacities={"x": 2, "y": 1, "z": 3})
    # neighbors = []
    # history = []
    # prices = {"x": 1, "y": 2, "z": 0}
    # excess_demand_vector = {"x": 0, "y": 2, "z": -2}
    # initial_budgets = {"ami": 5, "tami": 4, "tzumi": 3}
    # allocation = {"ami": ('x', 'y'), "tami": ('x', 'y')}
    # # find_individual_price_adjustment_neighbors(instance, neighbors, history, prices, excess_demand_vector,
    # #                                            initial_budgets, allocation)
    #
    # print(clipped_excess_demand(instance,prices,allocation))

    # instance = Instance(valuations={"ami": {"x": 3, "y": 4, "z": 2}, "tami": {"x": 4, "y": 3, "z": 2},
    #                                 "tzumi": {"x": 2, "y": 4, "z": 3}},
    #                     agent_capacities=2,
    #                     item_capacities={"x": 2, "y": 1, "z": 3})
    # neighbors = []
    # history = [
    #     {'x': 1, 'y': 2, 'z': 1}, {'x': 0, 'y': 0, 'z': 0}, {'x': 1, 'y': 0, 'z': 0},
    #     {'x': 0, 'y': 1, 'z': 0}, {'x': 0, 'y': 0, 'z': 1}, {'x': 1, 'y': 1, 'z': 0},
    #     {'x': 1, 'y': 0, 'z': 1}, {'x': 0, 'y': 1, 'z': 1}, {'x': 1, 'y': 1, 'z': 1},
    #     {'x': 0, 'y': 1, 'z': 2}, {'x': 0, 'y': 2, 'z': 1}, {'x': 1, 'y': 0, 'z': 2},
    #     {'x': 1, 'y': 2, 'z': 0}, {'x': 2, 'y': 0, 'z': 1}, {'x': 2, 'y': 1, 'z': 0},
    #     {'x': 2, 'y': 2, 'z': 0}, {'x': 2, 'y': 2, 'z': 1}, {'x': 1, 'y': 1, 'z': 2},
    #     {'x': 2, 'y': 1, 'z': 1}, {'x': 3, 'y': 0, 'z': 0}, {'x': 3, 'y': 1, 'z': 0},
    #     {'x': 3, 'y': 0, 'z': 1}, {'x': 3, 'y': 1, 'z': 1}, {'x': 0, 'y': 3, 'z': 0},
    #     {'x': 1, 'y': 3, 'z': 0}, {'x': 0, 'y': 0, 'z': 3}, {'x': 1, 'y': 0, 'z': 3},
    #     {'x': 2, 'y': 0, 'z': 3}, {'x': 3, 'y': 0, 'z': 3}, {'x': 4, 'y': 0, 'z': 3},
    #     {'x': 1, 'y': 4, 'z': 0}, {'x': 2, 'y': 3, 'z': 1}, {'x': 0, 'y': 5, 'z': 0}
    # ]
    # prices = {"x": 1, "y": 4, "z": 0}
    # excess_demand_vector = {"x": 1, "y": 0, "z": 0}
    # initial_budgets = {"ami": 5, "tami": 4, "tzumi": 3}
    # allocation = {"ami": ('x', 'y'), "tami": ('x', 'z'), "tzumi": ('x', 'z')}
    # # find_individual_price_adjustment_neighbors(instance, neighbors, history, prices, excess_demand_vector,
    # #                                            initial_budgets, allocation)
    #
    # allocation1 = {"ami": ('x', 'y'), "tami": ('x', 'z'), "tzumi": ('x', 'z')}
    # allocation2 = {"ami": ('x', 'y'), "tami": ('x', 'z'), "tzumi": ('x', 't')}
    # course = "z"
    # differ_in_one_value(allocation1, allocation2, course)

    # instance = Instance(valuations={"A":{"x":5, "y":4, "z":3, "w":2},"B":{"x":5, "y":2, "z":4, "w":3}},
    #      agent_capacities=3,
    #      item_capacities={"x":1, "y":2, "z":1, "w":2})
    # initial_budgets = {"A": 8, "B":6}
    # allocation = {"A": {'x', 'y','z'}, "B":{'x','y' ,'z'}}
    # equivalent_prices = find_all_equivalent_prices(instance, initial_budgets, [], allocation)
    # p = {"x":2, "y":4, "z":3, "w":0}
    # print(any([f(p) for f in equivalent_prices]))
    #
    # s1 = ['x', 'y', 'z']
    # s2 = ['x', 'y', 'z']
    # s3 = ['w', 'x', 'z']
    # h = []
    # h.append(lambda p: sum(p[key] for key in s1) <= 8)
    # h.append(lambda p: sum(p[key] for key in s2) <= 6)
    # h.append(lambda p: sum(p[key] for key in s3) >= 6)
    #
    # p = {"x":2, "y":4, "z":3, "w":0}
    # print(any([f(p) for f in h]))
