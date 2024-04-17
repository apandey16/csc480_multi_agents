# My additions: Plants which the prey eat and they grow in energy, hunters attack the predators, and prey run away from predators

from mesa import Agent, Model
import mesa
from mesa.datacollection import DataCollector
from mesa.experimental.jupyter_viz import JupyterViz
from mesa.time import RandomActivation
import seaborn as sns
from mesa.space import MultiGrid
import random
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import ChartModule


PLACEHOLDER_POS = (0, 0)
HEIGHT = 10
WIDTH = 10
PREY = 5
PREDATOR = 10
PLANT = 10
HUNTER = 10

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
        predator_agents = [agent for agent in possible_steps if
                       isinstance(agent, Predator)]
        if predator_agents:
            predator_to_run_from = random.choice(predator_agents)
            possible_steps.remove(predator_to_run_from)
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


class Hunter(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.energy = 100
        self.just_caught = False
        self.animals_caught = 0

    def move(self):
        if self.just_caught:
            self.just_caught = False
            return
        possible_steps = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False
        )
        predator_agents = [agent for agent in possible_steps if
                       isinstance(agent, Predator)]
        if predator_agents:
            predator_to_attack = random.choice(predator_agents)
            new_position = predator_to_attack.pos
        else:
            new_position = random.choice(possible_steps)
            self.model.grid.move_agent(self, new_position)

    def attack(self):
        predator_neighbors = self.model.grid.get_cell_list_contents(
            [self.pos]
        )
        predator_agents = [agent for agent in predator_neighbors if
                       isinstance(agent, Prey)]
        if predator_agents:
            predator_to_eat = random.choice(predator_agents)
            self.model.schedule.remove(predator_to_eat)
            self.model.grid.remove_agent(predator_to_eat)
            self.energy += predator_to_eat.energy
            self.just_caught = True
            self.animals_caught += 1

    def step(self):
        self.move()
        self.attack()
        self.energy -= 1

class Predator(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.energy = 100

    def move(self):
        possible_steps = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False
        )
        hunter_agents = [agent for agent in possible_steps if
                       isinstance(agent, Hunter)]
        if hunter_agents:
            hunter_to_run_from = random.choice(hunter_agents)
            possible_steps.remove(hunter_to_run_from)
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
        if self.pos is None:
            return
        self.move()
        self.eat()
        self.breed()
        self.energy -= 1

class PreyPredatorModel(Model):
    def __init__(self, height, width, prey_count, predator_count, plant_count, hunter_count):
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

        for i in range(hunter_count):
            hunter = Hunter(self.next_id(), self)
            self.grid.place_agent(hunter, PLACEHOLDER_POS)
            self.grid.move_to_empty(hunter)
            self.schedule.add(hunter)
        
        self.datacollector = DataCollector(model_reporters={
            "Prey": lambda m: sum(isinstance(agent, Prey) for agent in m.schedule.agents),
            "Predator": lambda m: sum(isinstance(agent, Predator) for agent in m.schedule.agents),
            "Plant": lambda m: sum(isinstance(agent, Plant) for agent in m.schedule.agents),
            "Hunter": lambda m: sum(isinstance(agent, Hunter) for agent in m.schedule.agents),
            }, agent_reporters={
            "Prey": "prey",
            "Predator": "predator",
            "Plant": "plant",
            "Hunter": "hunter",
            "Animals Caught": "animals_caught"
        }
        )

    def step(self):
        self.datacollector.collect(self)
        self.schedule.step()

def main():
    model = PreyPredatorModel(height=HEIGHT, width=WIDTH, prey_count=PREY, plant_count=PLANT, hunter_count=HUNTER,
                                predator_count=PREDATOR)

    for i in range(100):
        model.step()
        # Print population counts
        prey_count = sum(
            isinstance(agent, Prey) for agent in model.schedule.agents)
        predator_count = sum(
            isinstance(agent, Predator) for agent in model.schedule.agents)
        plant_count = sum(
            isinstance(agent, Plant) for agent in model.schedule.agents)
        hunter_count = sum(
            isinstance(agent, Hunter) for agent in model.schedule.agents)
        animals_caught = sum(agent.animals_caught for agent in model.schedule.agents if isinstance(agent, Hunter))
        print(f"After step {i}: Prey={prey_count}, Predators={predator_count}, Plants={plant_count}, Hunters={hunter_count}, Animals caught={animals_caught}")

    
        
if __name__ == '__main__':
    main()

def agent_portrayal(agent):
    portrayal = {"Shape": "circle", "Filled": "true", "r": 0.5, "layer": 0}
    if isinstance(agent, Predator):
        portrayal["color"] = "tab:red"
    elif isinstance(agent, Prey):
        portrayal["color"] = "tab:blue"
    elif isinstance(agent, Plant):
        portrayal["color"] = "tab:green"
    elif isinstance(agent, Hunter):
        portrayal["color"] = "tab:orange"
    print(portrayal)
    return portrayal

model_params ={
        "height": HEIGHT,
        "width": WIDTH,
        "prey_count": PREY,
        "predator_count": PREDATOR,
        "plant_count": PLANT,
        "hunter_count": HUNTER
    }

page = JupyterViz(
    PreyPredatorModel,
    model_params,
    measures=["Prey", "Predator", "Plant", "Hunter"],
    name="Predator/Prey Model",
    agent_portrayal=agent_portrayal,
)
# This is required to render the visualization in the Jupyter notebook
page
        