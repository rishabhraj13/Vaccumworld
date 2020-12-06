import vacuumworld
from vacuumworld.vwc import action, direction, orientation, colour, dirt, random
import math


class MyMind:
 

    def __init__(self):
        self.grid_size = 0
        self.orientation = None
        self.at_corner = False
        self.at_edge = False
        self.curr_pos = None
        self.max_grid_destination = None
        self.should_clean = 0  # 0: not yet cleaned, 1: set to clean, 2: cleaned
        self.destination = None
        self.colour = None
        self.name = None
        self.visited_locations = []  # Used to cache visited locations while grid size is unknown
        self.grid = []
        self.parsed_observations = []
        self.agent_colour_broadcast = 0                      # 0: not yet broadcast
                                                                #1: set to broadcast, 
                                                                #2: broadcast complete
        self.grid_size_broadcast = 0 
       
        self.give_way = None
        self.make_way_for_agent = None
        self.orientation_destination_order = "xy"

    def decide(self):
       
            
        for row in self.grid:
            print(row)

       
        # This is run in cycle 0 for agent discovery
        if self.agent_colour_broadcast == 1:
            print(" move to find grid size")
            return action.speak([0, self.parsed_observations, self.get_colour_code(self.colour)]), self.find_grid_size()

        if self.grid_size == 0:
            return action.speak([1, self.parsed_observations]), self.find_grid_size() if self.colour == "white" else action.idle()

     
        if self.grid_size_broadcast == 1:
            return action.speak([2, self.parsed_observations, self.grid_size])

        if not self.on_dest():
            return action.speak([1, self.parsed_observations]), self.move_to_destination()  if self.colour == "white" else action.idle()

        print('The graph has been traversed, Agent white is idle')
        return action.speak([1, self.parsed_observations]), action.idle()

    def find_grid_size(self):
        """
       used to find the grid size, grid size is determined by travelling to the edges 
        """
        
        if self.max_grid_destination == "south" and self.orientation != orientation.south:
            if self.orientation == orientation.north:
                return action.turn(direction.right)
            if self.orientation == orientation.west:
                return action.turn(direction.left)
            if self.orientation == orientation.east:
                return action.turn(direction.right)
       
        if self.max_grid_destination == "east" and self.orientation != orientation.east:
            if self.orientation == orientation.north:
                return action.turn(direction.right)
            if self.orientation == orientation.south:
                return action.turn(direction.left)
            if self.orientation == orientation.west:
                return action.turn(direction.right)

         
        if self.at_edge:
            return action.turn(direction.right)
       
        return action.move()

    def move_towards_dest(self, dest):
        
        if self.curr_pos.x < dest[0]:
            if self.orientation != orientation.east:
                if self.orientation == orientation.west:
                    return action.turn(direction.right)
                if self.orientation == orientation.north:
                    return action.turn(direction.right)
                if self.orientation == orientation.south:
                    return action.turn(direction.left)
              
            return action.move()

        if self.curr_pos.x > dest[0]:
            if self.orientation != orientation.west:
                if self.orientation == orientation.east:
                    return action.turn(direction.right)
                if self.orientation == orientation.north:
                    return action.turn(direction.left)
                if self.orientation == orientation.south:
                    return action.turn(direction.right)
               
            return action.move()


        if self.curr_pos.y > dest[1]:
            if self.orientation != orientation.north:
                if self.orientation == orientation.south:
                    return action.turn(direction.right)
                if self.orientation == orientation.west:
                    return action.turn(direction.right)
                if self.orientation == orientation.east:
                    return action.turn(direction.left)
            return action.move()
        
        if self.curr_pos.y < dest[1]:
            if self.orientation != orientation.south:
                if self.orientation == orientation.north:
                    return action.turn(direction.right)
                if self.orientation == orientation.west:
                    return action.turn(direction.left)
                if self.orientation == orientation.east:
                    return action.turn(direction.right)
            return action.move()





    def revise(self, observation, messages):
     
        if self.name is None:
            self.name = observation.center.agent.name
        if self.colour is None:
            self.colour = observation.center.agent.colour
       
        if self.agent_colour_broadcast == 0:
            self.agent_colour_broadcast = 1
            
        elif self.agent_colour_broadcast == 1:
            self.agent_colour_broadcast = 2
        else:
            pass

        self.curr_pos = observation.center.coordinate
        if self.check_forward_movement(observation):
            pass
        elif self.check_if_sides_are_none(observation):
            pass
        
        elif self.decision_at_corners(observation):
            pass
        else:
            self.at_edge = False
            self.at_corner = False
            if observation.forward.coordinate.x > observation.center.coordinate.x:
                self.orientation = orientation.east
            elif observation.forward.coordinate.x < observation.center.coordinate.x:
                self.orientation = orientation.west
            elif observation.forward.coordinate.y > observation.center.coordinate.y:
                self.orientation = orientation.south
            else:
                self.orientation = orientation.north
        
       
        self.parsed_observations = self.parse_observations(observation)
        self.update_grid_matrix(self.parsed_observations)

        self.check_messages(observation,messages)

        if self.grid_size == 0:
            self.check_at_corner(observation)
            self.check_at_edge(observation)
            if self.curr_pos.x > self.curr_pos.y:
                self.max_grid_destination = "east"
                return
            if self.curr_pos.x < self.curr_pos.y:
                self.max_grid_destination = "south"
                return
            if self.curr_pos.x == self.curr_pos.y:
                self.max_grid_destination = "east"
                return


        if self.grid_size > 0 and self.grid_size_broadcast == 1:
            self.grid_size_broadcast = 2

        if self.give_way and self.on_dest():
            
            self.give_way = None
        self.control_movement_logic(observation)

    def check_messages(self,observation,messages):
        for msg in messages:
            # print(self.colour + " " + str(msg.content[0]))
            if msg.content[0] == 0:
                self.update_grid_matrix(msg.content[1], msg.sender)
            elif msg.content[0] == 1:
                self.update_grid_matrix(msg.content[1], msg.sender)
            elif msg.content[0] == 2:
                self.grid_size = msg.content[2]
                self.grid = [[None for _ in range(self.grid_size)] for _ in range(self.grid_size)]
                self.update_grid_matrix(msg.content[1], msg.sender)

    def check_at_corner(self,observation):
        if self.at_corner:
            if observation.left is None:
                if  self.orientation == orientation.south or self.orientation == orientation.west :
                    self.grid_size = max(observation.center.coordinate.x, observation.center.coordinate.y) + 1
                    self.grid_size_broadcast = 1
                    self.grid = [[None for x in range(self.grid_size)] for y in range(self.grid_size)]
                    return
                if self.orientation == orientation.north and observation.forward:
                    self.grid_size = max(observation.center.coordinate.x, observation.center.coordinate.y) + 1
                    self.grid_size_broadcast = 1
                    self.grid = [[None for x in range(self.grid_size)] for y in range(self.grid_size)]
                    return
            if observation.right is None and observation.center.coordinate.x != 0 and (self.orientation is orientation.north or self.orientation is orientation.south or self.orientation is orientation.east):
                self.grid_size = max(observation.center.coordinate.x, observation.center.coordinate.y) + 1
                self.grid_size_broadcast = 1
                self.grid = [[None for x in range(self.grid_size)] for y in range(self.grid_size)]
                return
            
    def check_at_edge(self,observation):
         if self.at_edge:
            if observation.right is None and (
                    self.orientation is orientation.north or self.orientation is orientation.east):
                self.grid_size = max(observation.center.coordinate.x, observation.center.coordinate.y) + 1
                self.grid_size_broadcast = 1
                self.grid = [[None for x in range(self.grid_size)] for y in range(self.grid_size)]
                return
            elif (observation.left and observation.right) and (self.orientation is orientation.south or self.orientation is orientation.east):
                self.grid_size = max(observation.center.coordinate.x, observation.center.coordinate.y) + 1
                self.grid_size_broadcast = 1
                self.grid = [[None for x in range(self.grid_size)] for y in range(self.grid_size)]
                return
            elif observation.left is None and (self.orientation is orientation.south or self.orientation is orientation.west):
                self.grid_size = max(observation.center.coordinate.x, observation.center.coordinate.y) + 1
                self.grid_size_broadcast = 1
                self.grid = [[None for x in range(self.grid_size)] for y in range(self.grid_size)]
                return
            

    def move_to_destination(self):
        
        if self.give_way:
            dest=self.give_way
        else:
            dest=self.destination
        
        
        return self.move_towards_dest(dest)
    def control_movement_logic(self,observation):
        if observation.forward and observation.forward.agent:
            if int(self.name.split("-")[1]) > int(observation.forward.agent.name.split("-")[1]):
                if self.get_agent_free_observation(observation):
                    self.give_way = self.get_agent_free_observation(observation)
                    if self.orientation_destination_order == "xy":
                        self.orientation_destination_order = "yx"
                    else:
                        self.orientation_destination_order = "xy"
                    self.make_way_for_agent = 1
            elif self.opposite_orientation(observation.forward.agent.orientation) != self.orientation:
                self.give_way = self.get_agent_free_observation(observation)
                if self.orientation_destination_order == "xy":
                    self.orientation_destination_order = "yx"
                else:
                    self.orientation_destination_order = "xy"

        if self.destination is None or self.on_dest():
     
            closest_colour = self.get_closest(self.colour)
            closest_unexplored = self.get_closest()

            if closest_unexplored and closest_colour is None:
                self.destination = closest_unexplored
            elif closest_unexplored is None and closest_colour:
                self.destination = closest_colour
            elif closest_unexplored and closest_colour:
              
                if self.find_eucledian_distance((self.curr_pos.x, self.curr_pos.y), closest_colour) \
                        < self.find_eucledian_distance((self.curr_pos.x, self.curr_pos.y), closest_unexplored):
                    self.destination = closest_colour
                    return
               
                if self.find_eucledian_distance((self.curr_pos.x, self.curr_pos.y), closest_colour) \
                        > self.find_eucledian_distance((self.curr_pos.x, self.curr_pos.y), closest_unexplored):
                    self.destination = closest_unexplored
                    return
               
                if self.find_eucledian_distance((self.curr_pos.x, self.curr_pos.y), closest_colour) \
                        == self.find_eucledian_distance((self.curr_pos.x, self.curr_pos.y), closest_unexplored):
                    self.destination = closest_colour
                    return
            else:
                # no colour or unexplored
                return
            return
 

    def on_dest(self):
    
        return self.find_eucledian_distance((self.curr_pos.x, self.curr_pos.y), self.give_way) == 0.0 \
            if self.give_way \
            else self.find_eucledian_distance((self.curr_pos.x, self.curr_pos.y), self.destination) == 0.0

    
    def get_colour_code(self,obj):
    
        if obj:
            if type(obj) is dirt:
                d_clr = obj.colour 
            else:
                d_clr = obj
            if d_clr is colour.green:
                return "g"
            
            elif d_clr is colour.white:
                return "w"
            elif d_clr is colour.orange:
                return "o"
        return "n"

    def parse_observations(self, obs):
        
        list_obs=[]
        if self.should_clean == 0:
            list_obs.append((obs.center.coordinate.x, obs.center.coordinate.y, self.get_colour_code(obs.center.dirt)))
        else:
            list_obs.append((obs.center.coordinate.x, obs.center.coordinate.y, "n"))
        if (obs.left):
            list_obs.append((obs.left.coordinate.x, obs.left.coordinate.y, self.get_colour_code(obs.left.dirt)))
        else:
            list_obs.append(-1)
        if obs.forwardleft:
            list_obs.append((obs.forwardleft.coordinate.x, obs.forwardleft.coordinate.y, self.get_colour_code(obs.forwardleft.dirt)))
        else:
            list_obs.append(-1)
        if obs.forward:
            list_obs.append((obs.forward.coordinate.x, obs.forward.coordinate.y, self.get_colour_code(obs.forward.dirt)))
        else:
            list_obs.append(-1)
            
        if obs.forwardright:
            list_obs.append((obs.forwardright.coordinate.x, obs.forwardright.coordinate.y, self.get_colour_code(obs.forwardright.dirt)))
        else:
            list_obs.append(-1)
        if obs.right:
            list_obs.append((obs.right.coordinate.x, obs.right.coordinate.y, self.get_colour_code(obs.right.dirt)))
        else:
            list_obs.append(-1)
            
        return list_obs

    
    def update_grid_matrix(self, obs, ag=None):

        if len(self.grid) == 0:
            for o in obs:
                if type(o) is tuple:
                    self.visited_locations.append(o)
                continue
            return

        if len(self.visited_locations) > 0:
            for loc in self.visited_locations:
                self.grid[loc[1]][loc[0]] = loc[2]
            self.visited_locations = []

        for o in obs:
            if type(o) is tuple:
                self.grid[o[1]][o[0]] = o[2]
            continue
        
    def check_forward_movement(self,obs):
        if obs.forward == None and (obs.left and obs.right):
            self.at_edge = True
            self.at_corner = False
            if obs.left.coordinate.y == obs.right.coordinate.y:
                if obs.left.coordinate.x < obs.right.coordinate.x:
                    self.orientation = orientation.north
                else:
                    self.orientation = orientation.south
            else:
                if obs.left.coordinate.y < obs.right.coordinate.y:
                    self.orientation = orientation.east
                else:
                    self.orientation = orientation.west
            return True
        return False
    
    def check_if_sides_are_none(self,obs):
        if obs.forward == None and (obs.left is None or obs.right is None):
            self.at_edge = True
            self.at_corner = True
            if obs.left is None:
                if obs.center.coordinate.y == obs.right.coordinate.y:
                    if obs.center.coordinate.x < obs.right.coordinate.x:
                        self.orientation = orientation.north
                    else:
                        self.orientation = orientation.south
                else:
                    if obs.center.coordinate.y < obs.right.coordinate.y:
                        self.orientation = orientation.east
                    else:
                        self.orientation = orientation.west
            if obs.right == None:
                if obs.left.coordinate.x < obs.left.coordinate.y:
                    self.orientation = orientation.north
                else:
                    self.orientation = orientation.south
            return True
        return False
    def decision_at_corners(self,obs):
        if obs.left == None or obs.right == None:
            self.at_edge = True
            if obs.left == None:
                if obs.center.coordinate.y < obs.right.coordinate.y:
                    self.orientation = orientation.east
                elif obs.center.coordinate.y > obs.right.coordinate.y:
                    self.orientation = orientation.west
                elif obs.center.coordinate.x > obs.right.coordinate.x:
                    self.orientation = orientation.south
                else:
                    self.orientation = orientation.north
            else:
                if obs.center.coordinate.y < obs.left.coordinate.y:
                    self.orientation = orientation.west
                elif obs.center.coordinate.y > obs.left.coordinate.y:
                    self.orientation = orientation.east
                elif obs.center.coordinate.x > obs.left.coordinate.x:
                    self.orientation = orientation.north
                else:
                    self.orientation = orientation.south
            return True
        return False




    def get_closest(self, obj_type=None):
        """
        Gets the closest dirt or unexplored location using Euclidean distances
      
        """
        obj = self.get_colour_code(obj_type) if obj_type and self.get_colour_code(obj_type) != "n" else None

        locations = []
        for i in range(len(self.grid)):
            for j in range(len(self.grid)):
                if self.grid[i][j] is obj:
                    locations.append((j, i))

        if len(locations) == 0:
            return
        locations.sort(key=lambda x: self.find_eucledian_distance((self.curr_pos.x, self.curr_pos.y), x))
        # print(str(obj) + str(locations))
        return locations[0]

    def get_agent_free_observation(self, observation):
        """
        Gets one of the agent's observations that's in bounds and has no other agent occupying it
      
        """
        obs = [observation.left, observation.right, observation.forwardleft,
                observation.forwardright, observation.forward]
        ob = [o for o in obs if o and o.agent is None]
        if len(ob) == 0:
            return
        if self.destination:
            ob.sort(key=lambda o: self.find_eucledian_distance((o.coordinate.x, o.coordinate.y), self.destination))
            return ob[0].coordinate.x, ob[0].coordinate.y
        else:
            return ob[0].coordinate.x, ob[0].coordinate.y


    
    def opposite_orientation(self,orien):
        if orien is orientation.east:
            return orientation.west
        if orien is orientation.west:
            return orientation.east
        if orien is orientation.north:
            return orientation.south
        if orien is orientation.south:
            return orientation.north



   

    @staticmethod
    def find_eucledian_distance(x, y):
        return math.sqrt(math.pow((x[0] - y[0]), 2) + math.pow((x[1] - y[1]), 2))



vacuumworld.run(MyMind())
