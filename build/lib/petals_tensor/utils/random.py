import random
from typing import Collection, TypeVar

T = TypeVar("T")


def sample_up_to(population: Collection[T], k: int) -> T:
    """
    Samples up to k elements from a population
    Args:
        population: a collection of elements
        k: a number of elements to sample
    """
    if not isinstance(population, list):
        population = list(population)
    if len(population) > k:
        population = random.sample(population, k)
    return population
