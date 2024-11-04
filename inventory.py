import mesa
import pickle
import random

##############################
# COSTANTS ###################
##############################

AISLE_REPR = 1
PICK_LOCATION_REPR = 2
CHARGING_STATION_REPR = 3
ITEMS_PER_LOCATION = 4
NUMBER_OF_AISLES = 5
AISLE_LENGTH = 12
AVERAGE_LINES_PER_ORDER = 1.5


##############################
# CLASSES ####################
##############################

class Warehouse:
    def __init__(self, number_of_aisles: int, module_width: int, rack_depth: int, cross_aisle_width: int,
                 aisle_length: int, io_pos=(0, 0), charge_pos=(0, 1)):
        self.number_of_aisles = number_of_aisles
        self.aisle_length = aisle_length
        self.module_width = module_width
        self.rack_depth = rack_depth
        self.cross_aisle_width = cross_aisle_width
        self.io_pos = io_pos
        self.charge_pos = charge_pos
        self.width = self.module_width * self.number_of_aisles
        self.length = self.aisle_length + 2 * self.cross_aisle_width
        self.grid = [[0 for _ in range(self.width)] for _ in range(self.length)]
        self.grid = self._add_aisles_to_grid(aisle_seq=self._gen_aisles_list(), grid=self.grid)
        self.grid = self._add_io_pos(self.io_pos, self.grid)
        self.grid = self._add_charging_station(self.charge_pos, self.grid)
        self.locations = self._add_locations(aisle_seq=self._gen_aisles_list())
        self.inventory = self._add_inventory()

    def _gen_aisles_list(self):
        aisle_seq = [0, self.module_width - 1]
        for i in range(self.number_of_aisles - 1):
            aisle_seq += [aisle_seq[0 + i * 2] + self.module_width, aisle_seq[1 + i * 2] + self.module_width]
        return aisle_seq

    def _add_aisles_to_grid(self, aisle_seq, grid):
        aisle_seq = aisle_seq
        grid = grid
        for y, row in enumerate(grid[self.cross_aisle_width:-self.cross_aisle_width]):
            for x in aisle_seq:
                grid[y + self.cross_aisle_width][x] = AISLE_REPR
        return grid

    def _add_io_pos(self, io_pos, grid, placeholder = PICK_LOCATION_REPR):
        grid = grid
        grid[io_pos[1]][io_pos[0]] = placeholder
        return grid

    def _add_charging_station(self, charge_pos, grid, placeholder= CHARGING_STATION_REPR):
        grid = grid
        grid[charge_pos[1]][charge_pos[0]] = placeholder
        return grid

    def _add_locations(self, aisle_seq):
        locations_coordinates = [[x, y, z] for x in aisle_seq for y in
                                 range(self.cross_aisle_width, self.length - self.cross_aisle_width) for z in
                                 range(ITEMS_PER_LOCATION)]
        aisle_number = []
        for x in range(self.number_of_aisles):
            aisle_number += [1 + x] * self.aisle_length * 2 * ITEMS_PER_LOCATION
        location_list = []
        for idx, loc in enumerate(locations_coordinates):
            pick_x = loc[0] + 1 if loc[0] % 5 == 0 else loc[0] - 1
            item_loc = ItemLocation(idx, aisle_number[idx], [loc[0], loc[1], loc[2]], [pick_x, loc[1]])
            location_list.append(item_loc)
        return location_list

    def _add_inventory(self):
        locations = self.locations[:]
        random.shuffle(locations)
        weigths = [random.randrange(1, 20) / 10 for _ in locations]
        volumes = [random.randrange(1, 100) / 100 for _ in locations]
        inventory = []
        for idx, loc in enumerate(locations):
            it = Item(idx, [loc], weigths[idx], volumes[idx])
            inventory.append(it) 
        return inventory   
   
    def reshuffle(self,typology): #added
        locations = self.locations[:]
        inventory_reshuffle = []
        o_abc = pickle.load(open('abc_categories.pkl','rb'))
        if typology == 'vertical': 
            for idx, loc in enumerate(locations):
                if idx < 96:
                    o_abc.classa[idx].changelocation([loc])
                    o_abc.classa[idx].item_class('A')
                    inventory_reshuffle.append(o_abc.classa[idx])
                elif idx > 95 and idx < 240:
                    o_abc.classb[idx-96].changelocation([loc])
                    o_abc.classb[idx-96].item_class('B')
                    inventory_reshuffle.append(o_abc.classb[idx-96])
                else:
                    o_abc.classc[idx-240].changelocation([loc])
                    o_abc.classc[idx-240].item_class('C')
                    inventory_reshuffle.append(o_abc.classc[idx-240])  
        #if typology == 'horizontal':
            
        #print(inventory_reshuffle)
        self.inventory = inventory_reshuffle
        return inventory_reshuffle

    def __repr__(self):
        warehouse_map = ''
        # add legend
        warehouse_map += f"\n{'-' * 79}\nShelving: \t{AISLE_REPR}\nPicking position: \t{PICK_LOCATION_REPR}\nCharging station position:\t{CHARGING_STATION_REPR}\n{'-' * 79}\n"
        for row in self.grid:
            row_s = [str(x) for x in row]
            temp = ''.join(row_s) + '\n'
            warehouse_map += temp
        return warehouse_map


class ItemLocation:
    def __init__(self, item_location_id, aisle, location, picking_location):
        self.item_location_id = item_location_id
        self.location = location
        self.aisle = aisle
        self.picking_location = picking_location
        
    def get_location_x(self):
        return self.location[0]

    def get_location_y(self):
        return self.location[1]

    def get_location_z(self):
        return self.location[2]

    def get_picking_location_x(self):
        return self.picking_location[0]

    def get_picking_location_y(self):
        return self.picking_location[1]

    def __repr__(self):
        return f'Item id: {self.item_id} Location: {self.location} Picking location: {self.picking_location}'


class Item:
    def __init__(self, item_id, location: [ItemLocation], weight, volume):
        self.item_id = item_id
        self.location = location
        self.weight = weight
        self.volume = volume
        self.inv_class = None
    
    def changelocation(self,location_new): #added
        self.location = location_new #added
        o_order = pickle.load(open('orders_list.pkl','rb'))
        for order in o_order:
            for item in order.order_items:
                if self.item_id == item.item_id:
                    item.location = location_new
        with open('orders_list.pkl','wb') as file:
            pickle.dump(o_order,file)
        
        
    def item_class(self, classe):
        self.inv_class = classe
    def __repr__(self):
        return f'Item id: \t{self.item_id}  Location:\tx = {str(self.location[0].get_location_x())}, y = {str(self.location[0].get_location_y())}, z = {str(self.location[0].get_location_z())}  Weight: \t{self.weight}  Volume: \t{self.volume}\n class; {self.inv_class}'


class OrderItem(Item):
    def __init__(self, item_id, location: [ItemLocation], weight, volume, quantity):
        super().__init__(item_id, location, weight, volume)
        self.quantity = quantity
       

    def __repr__(self):
        return f'\nItem id: {self.item_id:>4}  Location:x = {str(self.location[0].get_location_x()):>2}| y = {str(self.location[0].get_location_y()):>2}| z = {str(self.location[0].get_location_z()):>2}  Weight: {self.weight:>4}  Volume: {self.volume:>4}  Quantity: {self.quantity:>2}  '


class ItemDataset:
    def __init__(self, warehouse, a=.2, b=.3, c=.5):
        self.warehouse = warehouse
        self.a = a
        self.b = b
        self.c = c
        self.classa = []
        self.classb = []
        self.classc = []
        self._gen_group()

    def _gen_group(self):
        inv = self.warehouse.inventory
        n = len(inv)
        self.classa = random.sample(inv, k=int(n * self.a))
        inv = list(set(inv) - set(self.classa))
        self.classb = random.sample(inv, k=int(n * self.b))
        inv = list(set(inv) - set(self.classb))
        self.classc = inv

class Order:
    def __init__(self, order_id, inv_cat):
        self.order_id = order_id
        self.inv_cat = inv_cat
        self.order_items = self.order_gen()

    def order_gen(self):
        order_items = []
        n_order_lines_prob = [1,2,3,4,4,5,5,6,6]
        n_items = random.choice(n_order_lines_prob)
        i = 0
        while i < n_items:
            item = random.choices([random.choice(self.inv_cat.classa), random.choice(self.inv_cat.classb),
                                   random.choice(self.inv_cat.classc)], weights=[0.7, 0.2, 0.1])[0]
            if order_items and any(it.item_id == item.item_id for it in order_items):
                pass
            else:
                quant = random.choice([1, 1, 2, 3])
                order_item = OrderItem(item_id=item.item_id, location=item.location, weight=item.weight, volume=item.volume, quantity=quant)
                order_items.append(order_item)
                i += 1
        return order_items

    def get_sorted_order(self):
        sorted_order = sorted(self.order_items, key=lambda item: (
        item.location[0].aisle, item.location[0].get_location_y(), item.location[0].get_location_x()))
        self.order_items = sorted_order
        return self

    def set_sorted_order(self):
        self.order_items = sorted(self.order_items, key=lambda item: (
        item.location[0].aisle, item.location[0].get_location_y(), item.location[0].get_location_x()))

    def order_pop(self, index=0):
        item = self.order_items.pop(index)
        return item

    def __repr__(self):
        order_ls = ""
        for item in self.order_items:
            order_ls += f"{item}\n" + "-" * 100 + "\n"
        return f'\nOrder id: {self.order_id}\n{"-" * 100}\nOrder items: \n\n{order_ls}'


##############################
# AGENTS #####################
##############################

class Picker(mesa.Agent):
    def __init__(self, picker_id, model, current_position, speed=0.95, pref_batch=False, linked_amr=None,
                 next_action="wait", path=[]):
        super().__init__(picker_id, model)
        self.current_pos = current_position
        self.speed = speed
        self.item = None
        self.order = None
        self.linked_amr = linked_amr
        self.next_action = next_action
        self.next_actions = [self.next_action]
        self.path = path
        self.pref_batch = pref_batch

    def compute_path(self, current_position, final_position):
        current_pos = current_position
        path = []
        module_width = self.model.warehouse.module_width
        if current_pos[0] // module_width == final_position[0] // module_width or list(current_pos) == [0, 0]:
            increment_x = -1 if final_position[0] <= current_pos[0] else 1
            for x in range(current_pos[0], final_position[0], increment_x):
                path.append([x + increment_x, current_pos[1]])
            if path: current_pos = path[-1]
            increment_y = -1 if final_position[1] <= current_pos[1] else 1
            for y in range(current_pos[1], final_position[1], increment_y):
                path.append([current_pos[0], y + increment_y])
        elif current_pos[0] // module_width != final_position[0] // module_width:
            lower_y_limit = self.model.warehouse.length
            entry = "upper" if final_position[1] + current_pos[1] <= lower_y_limit - final_position[1] + lower_y_limit - \
                               current_pos[1] else "lower"
            increment_x = -1 if final_position[0] <= current_pos[0] else 1
            if entry == "upper" and current_pos[1] not in [0,1]:
                top_limit = 1 if final_position[1] == 0 else self.model.warehouse.cross_aisle_width
                for y in range(current_pos[1], top_limit - 1, -1):
                    path.append([current_pos[0], y - 1])
                current_pos = path[-1]
                for x in range(current_pos[0], final_position[0], increment_x):
                    path.append([x + increment_x, current_pos[1]])
                current_pos = path[-1]
                for y in range(current_pos[1], final_position[1]):
                    path.append([current_pos[0], y + 1])
            if entry == "upper" and current_pos[1] in [0,1]:
                top_limit = self.model.warehouse.cross_aisle_width
                for y in range(current_pos[0], top_limit-1,1):
                    path.append([current_pos[0], y+1])
                current_pos = path[-1]
                for x in range(current_pos[0], final_position[0], increment_x):
                    path.append([x + increment_x, current_pos[1]])
                current_pos = path[-1]
                for y in range(current_pos[1], final_position[1]):
                    path.append([current_pos[0], y + 1])
            elif entry == "lower":
                for y in range(current_pos[1],self.model.warehouse.cross_aisle_width + self.model.warehouse.aisle_length):
                    path.append([current_pos[0], y + 1])
                current_pos = path[-1]
                for x in range(current_pos[0], final_position[0], increment_x):
                    path.append([x + increment_x, current_pos[1]])
                current_pos = path[-1]
                for y in range(current_pos[1], final_position[1], -1):
                    path.append([current_pos[0], y - 1])
        return path

    def step(self):
        self.next_action = self.next_actions.pop(0)
        if self.next_action == "wait":
            if self.model.orders and self.model.available_amr:
                self.order = self.model.orders.pop(0)
                self.linked_amr = self.model.available_amr.pop(0)
                self.item = self.order.order_pop(0)
                self.path = self.compute_path(self.current_pos, self.item.location[0].picking_location)
                self.linked_amr.linked_picker = self
                self.linked_amr.next_action = "path"
                if self.path:
                    self.next_actions += ["move"] * len(self.path)
                else:
                    self.next_actions += ["pick"] * sum(random.choice([1, 2]) for _ in range(self.item.quantity))
                    self.next_actions += ["unload"]
            else:
                self.next_actions += ["wait"]
        elif self.next_action == "move":
            if self.path:
                if random.choices([True, False], [self.speed, 1 - self.speed])[0]:
                    self.current_pos = self.path.pop(0)
                else:
                    self.next_actions.insert(0, "move")
            if not (self.path):
                self.next_actions += ["pick"] * sum(random.choice([1, 2]) for _ in range(self.item.quantity))
                self.next_actions += ["unload"]
        elif self.next_action == "pick":
            pass
        elif self.next_action == "unload":
            is_robot_ready = self.linked_amr.next_action == "load"
            if is_robot_ready:
                self.linked_amr.load_amr(self.item)
                self.item = None
                if self.order.order_items:
                    self.item = self.order.order_pop(0)
                    if self.item.location[0].picking_location[:2] == self.current_pos:
                        self.next_actions += ["pick"] * sum(
                            random.choice([1, 2]) for _ in range(self.item.quantity)) + ["unload"]
                    else:
                        self.path = self.compute_path(self.current_pos, self.item.location[0].picking_location)
                        self.next_actions += ["move"] * len(self.path)
                else:
                    self.next_actions += ["wait"]
            elif not(is_robot_ready):
                self.next_actions +=["unload"]

class Amr(mesa.Agent):
    def __init__(self, amr_id, model, current_position, linked_picker=None, next_action="wait"):
        super().__init__(amr_id, model)
        self.current_pos = current_position
        self.linked_picker = linked_picker
        self.carried_items = []
        self.next_action = next_action
        self.path = []
        self.capacity = 4

    def load_amr(self, item: OrderItem):
        self.carried_items.append(item)

    def compute_path(self, current_position, final_position):
        current_pos = current_position
        path = []
        module_width = self.model.warehouse.module_width
        if current_pos[0] // module_width == final_position[0] // module_width or list(current_pos) == [0, 0]:
            increment_x = -1 if final_position[0] <= current_pos[0] else 1
            for x in range(current_pos[0], final_position[0], increment_x):
                path.append([x + increment_x, current_pos[1]])
            if path: current_pos = path[-1]
            increment_y = -1 if final_position[1] <= current_pos[1] else 1
            for y in range(current_pos[1], final_position[1], increment_y):
                path.append([current_pos[0], y + increment_y])
        elif current_pos[0] // module_width != final_position[0] // module_width:
            lower_y_limit = self.model.warehouse.length
            entry = "upper" if final_position[1] + current_pos[1] <= lower_y_limit - final_position[1] + lower_y_limit - \
                               current_pos[1] else "lower"
            increment_x = -1 if final_position[0] <= current_pos[0] else 1
            if entry == "upper" and current_pos[1] not in [0, 1]:
                top_limit = 1 if final_position[1] == 0 else self.model.warehouse.cross_aisle_width
                for y in range(current_pos[1], top_limit - 1, -1):
                    path.append([current_pos[0], y - 1])
                current_pos = path[-1]
                for x in range(current_pos[0], final_position[0], increment_x):
                    path.append([x + increment_x, current_pos[1]])
                current_pos = path[-1]
                for y in range(current_pos[1], final_position[1]):
                    path.append([current_pos[0], y + 1])
            if entry == "upper" and current_pos[1] in [0, 1]:
                top_limit = self.model.warehouse.cross_aisle_width
                for y in range(current_pos[0], top_limit - 1, 1):
                    path.append([current_pos[0], y + 1])
                current_pos = path[-1]
                for x in range(current_pos[0], final_position[0], increment_x):
                    path.append([x + increment_x, current_pos[1]])
                current_pos = path[-1]
                for y in range(current_pos[1], final_position[1]):
                    path.append([current_pos[0], y + 1])
            elif entry == "lower":
                for y in range(current_pos[1],
                               self.model.warehouse.cross_aisle_width + self.model.warehouse.aisle_length):
                    path.append([current_pos[0], y + 1])
                current_pos = path[-1]
                for x in range(current_pos[0], final_position[0], increment_x):
                    path.append([x + increment_x, current_pos[1]])
                current_pos = path[-1]
                for y in range(current_pos[1], final_position[1], -1):
                    path.append([current_pos[0], y - 1])
        return path

    def compute_path_return(self, current_position, final_pos):
        current_pos = current_position
        path = []
        for y in range(current_pos[1], final_pos[1], -1):
            path.append([current_pos[0], y-1])
        current_pos = path[-1]
        for x in range(current_pos[0],final_pos[0], -1):
            path.append([x-1, current_pos[1]])
        return path

    def step(self):
        if self.next_action == "wait":
            pass
        elif self.next_action == "path":
            self.path = self.compute_path(self.current_pos, self.linked_picker.item.location[0].picking_location)
            self.next_action = "move"
        elif self.next_action == "move":
            self.current_pos = self.path.pop(0)
            if not self.path:
                self.next_action = "load"
        elif self.next_action == "load":
            if self.linked_picker.next_actions[0] == "wait":
                self.linked_picker.linked_amr = None
                self.linked_picker = None
                self.next_action = "return"
                self.path = self.compute_path_return(self.current_pos, self.model.warehouse.io_pos)
            else:
                self.path = self.compute_path(self.current_pos, self.linked_picker.item.location[0].picking_location)
                if self.path:
                    self.next_action = "move"
                else:
                    self.next_action = "load"
        elif self.next_action == "return":
            self.current_pos = self.path.pop(0)
            if not (self.path):
                self.next_action = "unload"
        elif self.next_action == "unload":
            self.carried_items = []
            self.next_action = "wait"
            self.model.available_amr.append(self)

##############################
# MODEL ######################
##############################

class WarehouseModel(mesa.Model):
    def __init__(self, warehouse, n_pickers, n_amr, orders):
        super().__init__()
        self.warehouse = warehouse
        self.n_pickers = n_pickers
        self.n_amr = n_amr
        self.available_amr = []
        self.schedule = mesa.time.BaseScheduler(self)
        self.orders = [order.get_sorted_order() for order in orders]


        for picker_id in range(self.n_pickers):
            picker = Picker(picker_id=picker_id, model=self, current_position=self.warehouse.io_pos)
            self.schedule.add(picker)

        for amr_id in range(self.n_amr):
            amr = Amr(amr_id=n_pickers + amr_id, model=self, current_position=self.warehouse.io_pos)
            self.available_amr.append(amr)
            self.schedule.add(amr)

    def step(self):
        self.schedule.step()

typology = 'vertical' # added 
o_orders = pickle.load(open('orders_list.pkl', 'rb'))
o_warehouse = pickle.load(open('warehouse.pkl', 'rb'))
warehousenew = Warehouse(5,5,1,4,12)
warehousenew.reshuffle(typology)
o_warehousemodel = WarehouseModel(warehouse=warehousenew, n_pickers=2, n_amr=2, orders=o_orders)
#print(o_orders)
#print(warehousenew.inventory)



step = 0
with open("orders.txt", "w") as of:
    for order in o_orders:
        of.write(str(order)+"\n")

with open("log.txt", "w") as rf:
    while o_warehousemodel.orders or not (
    all([x.next_actions[0] == "wait" for x in o_warehousemodel.agents_by_type[Picker]])) or not (
    all(x.next_action == "wait" for x in o_warehousemodel.agents_by_type[Amr])):
        step += 1
        o_warehousemodel.step()
        rf.write(f"\nStep:  {step}\n")
        rf.write("\n" + "-" * 79 +"\n")
        rf.write("Pickers\n")
        for picker in o_warehousemodel.agents_by_type[Picker]:
            rf.write("\n" + f"Picker: {picker.unique_id}")
            rf.write("\n\t" + "Picker position: " + str(picker.current_pos))
            if picker.item: rf.write("\n\t" + f"Item id: {picker.item.item_id}")
            rf.write("\n\t" + "Picker path: " + str(picker.path))
            rf.write("\n\t" + "Picker next actions: " + str(picker.next_actions))
            rf.write("\n" + "-" * 20)
        rf.write("\n" + "-" * 79+"\n")

        rf.write("Amrs\n")
        for amr in o_warehousemodel.agents_by_type[Amr]:
            rf.write("\n" + f"Amr: {amr.unique_id}")
            rf.write("\n\t" + "Amr position: " + str(amr.current_pos))
            rf.write("\n\t" + "Amr path: " + str(amr.path))
            rf.write("\n\t" + "Amr next action: " + str(amr.next_action))
            rf.write("\n\t" + "Amr carried items: " + str(amr.carried_items))
            rf.write("\n" + "-" * 20 + "\n")
        rf.write("\n" + "-" * 79)
        rf.write("\n" + "#" * 79 + "\n" +"#" * 79 )
    print (f"Total number of steps [s]: {step}\nTotal time [h]: {step//3600} h - {(step % 3600)// 60} m")