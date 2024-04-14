# p1 fixed original code:
# - in PredatorPreyModel __init__() function, called super init and initialized current_id to 0
# - replaced deprecated find_empty() function by placing agents at (0, 0) and using move_to_empty()
# - to prevent Prey move() errors, made step() return early if self.pos is None

# My addition: 

from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
import random


PLACEHOLDER_POS = (0, 0)

class Plant(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.energy = 50
    
    def grow(self):
        self.energy += 1

    def step(self):
        if self.pos is None:
            return
        self.grow()

class Prey(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.energy = 100

    def move(self):
        possible_steps = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False
        )
        new_position = random.choice(possible_steps)
        self.model.grid.move_agent(self, new_position)

    def eat(self):
        plant_neighbors = self.model.grid.get_cell_list_contents(
            [self.pos]
        )
        plant_agents = [agent for agent in plant_neighbors if
                       isinstance(agent, Plant)]
        if plant_agents:
            plant_to_eat = random.choice(plant_agents)
            self.model.schedule.remove(plant_to_eat)
            self.model.grid.remove_agent(plant_to_eat)
            self.energy += plant_to_eat.energy

    def breed(self):
        if self.energy >= 200:
            self.energy -= 100
            new_prey = Prey(self.model.next_id(), self.model)
            self.model.grid.place_agent(new_prey, PLACEHOLDER_POS)
            self.model.grid.move_to_empty(new_prey)
            self.model.schedule.add(new_prey)

    def step(self):
        # if this agent was removed from the grid, don't step. this is
        # important because if an agent is removed from the RandomActivation
        # scheduler before it has stepped, it will still step one last time
        if self.pos is None:
            return
        self.move()
        self.eat()
        self.breed()
        self.energy -= 1


class Predator(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.energy = 100

    def move(self):
        possible_steps = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False
        )
        new_position = random.choice(possible_steps)
        self.model.grid.move_agent(self, new_position)

    def eat(self):
        prey_neighbors = self.model.grid.get_cell_list_contents(
            [self.pos]
        )
        prey_agents = [agent for agent in prey_neighbors if
                       isinstance(agent, Prey)]
        if prey_agents:
            prey_to_eat = random.choice(prey_agents)
            self.model.schedule.remove(prey_to_eat)
            self.model.grid.remove_agent(prey_to_eat)
            self.energy += 100

    def breed(self):
        if self.energy >= 200:
            self.energy -= 100
            new_predator = Predator(self.model.next_id(), self.model)
            self.model.grid.place_agent(new_predator, PLACEHOLDER_POS)
            self.model.grid.move_to_empty(new_predator)
            self.model.schedule.add(new_predator)

    def step(self):
        self.move()
        self.eat()
        self.breed()
        self.energy -= 1


class PreyPredatorModel(Model):
    def __init__(self, height, width, prey_count, predator_count, plant_count):
        super().__init__()
        self.current_id = 0
        self.height = height
        self.width = width
        self.grid = MultiGrid(height, width, torus=True)
        self.schedule = RandomActivation(self)
        self.running = True

        for i in range(prey_count):
            prey = Prey(self.next_id(), self)
            self.grid.place_agent(prey, PLACEHOLDER_POS)
            self.grid.move_to_empty(prey)
            self.schedule.add(prey)

        for i in range(predator_count):
            predator = Predator(self.next_id(), self)
            self.grid.place_agent(predator, PLACEHOLDER_POS)
            self.grid.move_to_empty(predator)
            self.schedule.add(predator)

        for i in range(plant_count):
            plant = Plant(self.next_id(), self)
            self.grid.place_agent(plant, PLACEHOLDER_POS)
            self.grid.move_to_empty(plant)
            self.schedule.add(plant)

    def step(self):
        self.schedule.step()

def main():
    model = PreyPredatorModel(height=10, width=100, prey_count=50, plant_count=10,
                              predator_count=10)

    for i in range(100):
        model.step()
        # Print population counts
        prey_count = sum(
            isinstance(agent, Prey) for agent in model.schedule.agents)
        predator_count = sum(
            isinstance(agent, Predator) for agent in model.schedule.agents)
        plant_count = sum(
            isinstance(agent, Plant) for agent in model.schedule.agents)
        print(f"After step {i}: Prey={prey_count}, Predators={predator_count}, Plants={plant_count}")


if __name__ == '__main__':
    main()
