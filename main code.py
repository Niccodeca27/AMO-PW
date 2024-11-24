import mesa
import pickle
import random
random.seed(42)
from collections import defaultdict
from sklearn.cluster import KMeans
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from sklearn.preprocessing import StandardScaler
# from sklearn_extra.cluster import KMedoids
import os
from matplotlib.patches import FancyArrowPatch

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

def distance_compute_path(current_position, final_position, module_width=5, warehouse_length=12, cross_aisle_width=4, aisle_length=25):
    current_pos = current_position
    path = []
    distance_walked = 0

    # Verifica si el picker y el item están en el mismo módulo (pasillo) o en la posición de origen
    if current_pos[0] // module_width == final_position[0] // module_width or list(current_pos) == [0, 0]:
        increment_x = -1 if final_position[0] <= current_pos[0] else 1
        for x in range(current_pos[0], final_position[0], increment_x):
            path.append([x + increment_x, current_pos[1]])
            distance_walked += 1

        if path:
            current_pos = path[-1]

        increment_y = -1 if final_position[1] <= current_pos[1] else 1
        for y in range(current_pos[1], final_position[1], increment_y):
            path.append([current_pos[0], y + increment_y])
            distance_walked += 1

    # Si el picker y el item están en módulos diferentes
    elif current_pos[0] // module_width != final_position[0] // module_width:
        lower_y_limit = warehouse_length
        entry = "upper" if final_position[1] + current_pos[1] <= lower_y_limit - final_position[1] + lower_y_limit - current_pos[1] else "lower"

        increment_x = -1 if final_position[0] <= current_pos[0] else 1

        if entry == "upper" and current_pos[1] not in [0, 1]:
            top_limit = 1 if final_position[1] == 0 else cross_aisle_width
            for y in range(current_pos[1], top_limit - 1, -1):
                path.append([current_pos[0], y - 1])
                distance_walked += 1
            current_pos = path[-1]

            for x in range(current_pos[0], final_position[0], increment_x):
                path.append([x + increment_x, current_pos[1]])
                distance_walked += 1
            current_pos = path[-1]

            for y in range(current_pos[1], final_position[1]):
                path.append([current_pos[0], y + 1])
                distance_walked += 1

        if entry == "upper" and current_pos[1] in [0, 1]:
            top_limit = cross_aisle_width
            for y in range(current_pos[0], top_limit - 1, 1):
                path.append([current_pos[0], y + 1])
                distance_walked += 1
            current_pos = path[-1]

            for x in range(current_pos[0], final_position[0], increment_x):
                path.append([x + increment_x, current_pos[1]])
                distance_walked += 1
            current_pos = path[-1]

            for y in range(current_pos[1], final_position[1]):
                path.append([current_pos[0], y + 1])
                distance_walked += 1

        elif entry == "lower":
            for y in range(current_pos[1], cross_aisle_width + aisle_length):
                path.append([current_pos[0], y + 1])
                distance_walked += 1
            current_pos = path[-1]

            for x in range(current_pos[0], final_position[0], increment_x):
                path.append([x + increment_x, current_pos[1]])
                distance_walked += 1
            current_pos = path[-1]

            for y in range(current_pos[1], final_position[1], -1):
                path.append([current_pos[0], y - 1])
                distance_walked += 1

    #print(path)
    
    return  distance_walked
import os

def save_figure(image_path, fig):
    # Obtener la ruta de la carpeta
    directory = os.path.dirname(image_path)
    
    # Verificar si la carpeta existe; si no, crearla
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    # Guardar la figura
    fig.savefig(image_path)  
    plt.close(fig)


##############################
# CLASSES ####################
##############################
#this class represents the warehouse (physical space and functions)
#to create a warehouse you need number of aisle, module widht, rack depth, cross aisle widht, and aisle lenght, plus the position of the i/o point and the charging point
class Warehouse:
    def __init__(self, number_of_aisles: int, module_width: int, rack_depth: int, cross_aisle_width: int,
                 aisle_length: int):
        
## AGGIUNTO DIVERSE POSIZIONI DELL'I/O E FATTO IN MODO CHE NELLA STESSA POSIZIONE DELL'I/O L'AMR SI POSSA RICARICARE
        
        # basic warehouse parameters
        self.number_of_aisles = number_of_aisles
        self.aisle_length = aisle_length
        self.module_width = module_width
        self.rack_depth = rack_depth
        self.cross_aisle_width = cross_aisle_width
        
        self.width = self.module_width * self.number_of_aisles
        self.length = self.aisle_length + 2 * self.cross_aisle_width
        
        # Configure I/O positions based on io_config parameter
        # self.io_positions = self._set_io_positions(io_config)
        # Set charging positions to be the same as I/O positions
        self.cuenta = 0
        
        # create the grid
        self.grid = [[0 for _ in range(self.width)] for _ in range(self.length)]
        
        # populate the grid
        self.grid = self._add_aisles_to_grid(aisle_seq=self._gen_aisles_list(), grid=self.grid)
        self.grid = self._add_io_and_charging_positions(self.io_positions, self.grid)
        self.locations = self._add_locations(aisle_seq=self._gen_aisles_list())
        self.inventory = self._add_inventory()
        
        
    def _gen_aisles_list(self):
            #this creates a list with the position of the different aisles based on the module width
            aisle_seq = [0, self.module_width - 1]
            for i in range(self.number_of_aisles - 1):
                #each item of the list has the position of the beggining of the aisle, and the position of the end of the aisle
                aisle_seq += [aisle_seq[0 + i * 2] + self.module_width, aisle_seq[1 + i * 2] + self.module_width]
            return aisle_seq

    def _add_aisles_to_grid(self, aisle_seq, grid):
            aisle_seq = aisle_seq
            grid = grid
            #it adds the aisles to the grid
            #it iterates in the rows of the grid, excluding the cross aisles
            
            for y, row in enumerate(grid[self.cross_aisle_width:-self.cross_aisle_width]):
                for x in aisle_seq:
                    #in the position of the aisles, it adds the corresponding representation of the aisle
                    grid[y + self.cross_aisle_width][x] = AISLE_REPR
            return grid

    def _set_io_positions(self, io_config: str) -> list:
        """
        Determina le posizioni I/O basate sulla configurazione specificata
        
        Args:
            io_config: può essere 'left', 'centered', o 'full'
            
        Returns:
            Lista di tuple con le coordinate (x,y) delle posizioni I/O
        """
        self.io_positions = []
        if io_config == 'left':
            self.io_positions = [(0, 0)]
        elif io_config == 'centered':
            self.io_positions= [(int((self.width-1)/2), 0)]  # reso dinamico usando self.width
        elif io_config == 'full':
            self.io_positions =  [(x, 0) for x in range(self.width)]
        else:
            raise ValueError("io_config deve essere 'left', 'centered', o 'full'")
        self.charge_positions = self.io_positions

# PER CONTROLLARE SE E' GIUSTO DOVE METTE L'I/O
#        Aggiunge le posizioni I/O e di ricarica al grid (stesse posizioni)
#        Args:
#            positions: lista di tuple (x,y) per le posizioni I/O e di ricarica
#            grid: il grid corrente del magazzino      
#        Returns: Grid aggiornato con le posizioni I/O e di ricarica
    def _add_io_and_charging_positions(self, positions: list, grid: list) -> list:
        for x, y in positions:
            grid[y][x] = 3  # usando 3 per indicare una posizione che è sia I/O che charging
        return grid

#    Restituisce tutte le posizioni che sono sia I/O che charging
    def get_io_and_charge_positions(self):
        return self.io_positions

#    Verifica se una posizione è sia punto I/O che charging
    def is_io_and_charge_point(self, position: tuple) -> bool:
        return position in self.io_positions

    def _add_locations(self, aisle_seq):
        #this methods is for generate the picking position in the aisles
        #in each location can be ITEMS PER LOCATION (4 in this case) items (this represents the z axes depth)
        #the possible location in the x axis it's giving for the different aisles position listed in aisle seq for the ailse 1, the position would be 0, for the aisle 1 the position would be 5 (because of the module)
        #the possible position in the y axes corresponds the position where the upper cross aisle begins until the lower cross aisles begin
        locations_coordinates = [[x, y, z] for x in aisle_seq for y in
                                 range(self.cross_aisle_width, self.length - self.cross_aisle_width) for z in
                                 range(ITEMS_PER_LOCATION)]
        #ex of output of this considering aisle_seq =[0,5,10], cross_aisle_width = 2, 3 items per location
        '''
        locations_coordinates = [
            # Para x = 0
            [0, 2, 0], [0, 2, 1], [0, 2, 2],
            [0, 3, 0], [0, 3, 1], [0, 3, 2],
            [0, 4, 0], [0, 4, 1], [0, 4, 2],
            [0, 5, 0], [0, 5, 1], [0, 5, 2],
            [0, 6, 0], [0, 6, 1], [0, 6, 2],
            [0, 7, 0], [0, 7, 1], [0, 7, 2],
            [0, 8, 0], [0, 8, 1], [0, 8, 2],

            # Para x = 5
            [5, 2, 0], [5, 2, 1], [5, 2, 2],
            [5, 3, 0], [5, 3, 1], [5, 3, 2],
            [5, 4, 0], [5, 4, 1], [5, 4, 2],
            [5, 5, 0], [5, 5, 1], [5, 5, 2],
            [5, 6, 0], [5, 6, 1], [5, 6, 2],
            [5, 7, 0], [5, 7, 1], [5, 7, 2],
            [5, 8, 0], [5, 8, 1], [5, 8, 2],

            # Para x = 10
            [10, 2, 0], [10, 2, 1], [10, 2, 2],
            [10, 3, 0], [10, 3, 1], [10, 3, 2],
            [10, 4, 0], [10, 4, 1], [10, 4, 2],
            [10, 5, 0], [10, 5, 1], [10, 5, 2],
            [10, 6, 0], [10, 6, 1], [10, 6, 2],
            [10, 7, 0], [10, 7, 1], [10, 7, 2],
            [10, 8, 0], [10, 8, 1], [10, 8, 2]
        ]
        '''

        aisle_number = []
        #x represents the id of the aisle
        for x in range(self.number_of_aisles):
            #add one to get the number of the aisle
            #there is two line of locations (on of each side of the aisle), this would generate 8 possible locations per aisle, where each one is represented by x+1
            aisle_number += [1 + x] * self.aisle_length * 2 * ITEMS_PER_LOCATION
        
        location_list = []

        #iterate in the locations
        for idx, loc in enumerate(locations_coordinates):
            #calculate the position 
            #5 should be self.modul_width
            #loc[0] es la coordenada x de location_coordinattes, mueve la posicion una a la derecha ( o una a la izquierda) para crear la ubicacion del item
            pick_x = loc[0] + 1 if loc[0] % 5 == 0 else loc[0] - 1
            #crea el itemlocation, con el indice respectivo, las coordenadas respectivas del item position, y las ubicaciones de los items dentro del item location
            item_loc = ItemLocation(idx, aisle_number[idx], [loc[0], loc[1], loc[2]], [pick_x, loc[1]])
            location_list.append(item_loc)
        return location_list

    def _add_inventory(self):
        #creates a copy of the list
        locations = self.locations[:]
        #it makes them random
        random.shuffle(locations)
        #the weight and volume of the items is random in the ranges given
        weigths = [random.randrange(1, 20) / 10 for _ in locations]
        volumes = [random.randrange(1, 100) / 100 for _ in locations]
        inventory = []
        #it saves items random
        for idx, loc in enumerate(locations):
            #creates an item, and saves them in the random location
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
        elif typology == 'horizontal':
            i = 0
            j = 0
            k = 0
            for idx, loc in enumerate(locations):
                ranges_a = [(0, 12),(48, 60),(96, 108),(144, 156),(192, 200),(240, 248),(288, 296),(336, 344),(384, 392),(432, 440)]
                ranges_b = [(12, 24),(60, 72),(108, 120),(156, 168),(200, 216),(248, 264),(296, 312),(344, 360),(392, 408),(440, 456)]
                if any(start <= idx < end for start, end in ranges_a):
                    o_abc.classa[i].changelocation([loc])
                    o_abc.classa[i].item_class('A')
                    inventory_reshuffle.append(o_abc.classa[i])
                    i = i + 1
                elif any(start <= idx < end for start, end in ranges_b):
                    o_abc.classb[j].changelocation([loc])
                    o_abc.classb[j].item_class('B')
                    inventory_reshuffle.append(o_abc.classb[j])
                    j = j + 1
                else:
                    o_abc.classc[k].changelocation([loc])
                    o_abc.classc[k].item_class('C')
                    inventory_reshuffle.append(o_abc.classc[k])
                    k = k + 1
        elif typology == 'oblique':
            i = 0
            j = 0
            k = 0
            for idx, loc in enumerate(locations):
                ranges_a = [(0, 40),(48, 76),(96, 116),(144, 152)]
                ranges_b = [(40, 48),(76, 96),(116, 144),(152, 224),(240, 256)]
                if any(start <= idx < end for start, end in ranges_a):
                    o_abc.classa[i].changelocation([loc])
                    o_abc.classa[i].item_class('A')
                    inventory_reshuffle.append(o_abc.classa[i])
                    i = i + 1
                elif any(start <= idx < end for start, end in ranges_b):
                    o_abc.classb[j].changelocation([loc])
                    o_abc.classb[j].item_class('B')
                    inventory_reshuffle.append(o_abc.classb[j])
                    j = j + 1
                else:
                    o_abc.classc[k].changelocation([loc])
                    o_abc.classc[k].item_class('C')
                    inventory_reshuffle.append(o_abc.classc[k])
                    k = k + 1
        elif typology == 'double_oblique': ##like oblique but in the center (for central I/O)
            i = 0
            j = 0
            k = 0
            for idx, loc in enumerate(locations):
                ranges_a = [(96,100),(144,160),(192,220),(240,268),(288,304),(336,340)]
                ranges_b = [(0,4),(48,60),(100,120),(160,176),(220,240),(268,288),(304,320),(340,360),(384,396),(432,436)]
                if any(start <= idx < end for start, end in ranges_a):
                    o_abc.classa[i].changelocation([loc])
                    o_abc.classa[i].item_class('A')
                    inventory_reshuffle.append(o_abc.classa[i])
                    i = i + 1
                elif any(start <= idx < end for start, end in ranges_b):
                    o_abc.classb[j].changelocation([loc])
                    o_abc.classb[j].item_class('B')
                    inventory_reshuffle.append(o_abc.classb[j])
                    j = j + 1
                else:
                    o_abc.classc[k].changelocation([loc])
                    o_abc.classc[k].item_class('C')
                    inventory_reshuffle.append(o_abc.classc[k])
                    k = k + 1
        elif typology == 'original':
            warehouse = pickle.load(open('warehouse_original.pkl','rb'))
            inventory_reshuffle = warehouse.inventory
            #print(o_abc.classa)
            lista_ids_a = [item.item_id  for item in o_abc.classa]
            lista_ids_b  = [item.item_id  for item in o_abc.classb]
            lista_ids_c = [item.item_id  for item in o_abc.classc]
            for item in inventory_reshuffle:
                
                if item.item_id  in lista_ids_a:
                    item.item_class('A')
                elif item.item_id  in lista_ids_b:
                    item.item_class('B')
                else:
                    item.item_class('C')
                #print(item)
        #print(inventory_reshuffle)
        elif typology == 'double_horizontal':
            i = 0
            j = 0
            k = 0
            for idx, loc in enumerate(locations):
                ranges_a = [(0, 8),(44, 56),(92, 104),(140, 152),(188, 196),(236, 244),(284, 292),(332, 340),(380, 388),(428, 436),(476, 480)]
                ranges_b = [(8, 12),(36, 44),(56, 60),(84, 92),(104, 108),(132, 140),(152, 156),(180, 188),(196, 204),(228, 236),(244, 252),(276, 284),(292, 300),(324, 332),(340, 348),(372, 380),(388, 396),(420, 428),(436, 444),(468, 476)]
                if any(start <= idx < end for start, end in ranges_a):
                    o_abc.classa[i].changelocation([loc])
                    o_abc.classa[i].item_class('A')
                    inventory_reshuffle.append(o_abc.classa[i])
                    i = i + 1
                elif any(start <= idx < end for start, end in ranges_b):
                    o_abc.classb[j].changelocation([loc])
                    o_abc.classb[j].item_class('B')
                    inventory_reshuffle.append(o_abc.classb[j])
                    j = j + 1
                else:
                    o_abc.classc[k].changelocation([loc])
                    o_abc.classc[k].item_class('C')
                    inventory_reshuffle.append(o_abc.classc[k])
                    k = k + 1

        self.inventory = inventory_reshuffle
        return inventory_reshuffle

    def __repr__(self):
        #this is to print out the warehouse map
        #1 is rack, 0 is nothing, 2 i/o, 3 is the chargig station
        warehouse_map = ''
        # add legend
        print(self.module_width)
        warehouse_map += f"\n{'-' * 79}\nShelving: \t{AISLE_REPR}\nPicking position: \t{PICK_LOCATION_REPR}\nCharging station position:\t{CHARGING_STATION_REPR}\n{'-' * 79}\n"
        for row in self.grid:
            row_s = [str(x) for x in row]
            temp = ''.join(row_s) + '\n'
            warehouse_map += temp
        return warehouse_map
    def plot_warehouse(self, path=None, picker_id=None,  start_pos=None, end_pos=None):
        self.cuenta[picker_id]+=1
        """
        Grafica el diseño del warehouse, mostrando las ubicaciones de los distintos elementos y los caminos de los pickers.
        
        paths: diccionario donde la clave es el id del picker y el valor es la lista de coordenadas del camino de ese picker.
        picker_id: El id del picker para asignar un color único.
        """
        grid = np.array(self.grid)
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Colores suaves para el warehouse
        cmap = plt.cm.Pastel2  # Cambia a una paleta de colores suaves
        #print(self.grid)
        ax.imshow(self.grid, cmap=cmap, extent=[0, grid.shape[1], grid.shape[0], 0], interpolation='nearest')
        
        if hasattr(self, 'io_positions') and self.io_positions:
            for io_point in self.io_positions:
                x, y = io_point
                ax.plot(
                    x + 0.5, y + 0.5,  # Centrar el marcador en la celda
                    marker='s', color='black', markersize=12, label='I/O POINT'
                )

        # Leyenda personalizada
        handles = [
            plt.Line2D([0], [0], marker='s', color='w', markerfacecolor='honeydew', markersize=10, label='Charging Station'),
            plt.Line2D([0], [0], marker='s', color='w', markerfacecolor='black', markersize=10, label='I/O Point')
        ]
        ax.legend(handles=handles, loc='upper left')

        # Configuración de la cuadrícula
        ax.set_xticks(np.arange(0, grid.shape[1], step=self.module_width))
        ax.set_yticks(np.arange(0, grid.shape[0], step=self.cross_aisle_width))
        ax.grid(color='lightgrey', linestyle='--', linewidth=0.5)
        class_colors = {
        'A': 'lightgoldenrodyellow',
        'B': 'lightsteelblue',
        'C': 'lightcoral'
        }
        for class_type, color in class_colors.items():
            handles.append(plt.Line2D([0], [0], marker='s', color='w', markerfacecolor=color, markersize=10, label=f'Class {class_type} Inventory'))
        if self.inventory:
            
            for item in self.inventory:
                #print(item)
                
                x = item.location[0].get_location_x()
                y = item.location[0].get_location_y()
                #print(x,y)
                ax.add_patch(plt.Rectangle((x, y), 1, 1, color=class_colors[item.inv_class]))
        
        ax.legend(handles=handles, loc='upper left')
        # Graficar los paths de los pickers si están disponibles
        if path:
            # Asignar un color único basado en el id del picker
            path_color = plt.cm.get_cmap('tab20', 20)(picker_id % 20)  # Usando una paleta de 20 colores
            
            # Graficar los pasos hasta el penúltimo paso
            for (x, y) in path[:-1]:
                ax.plot(x + 0.5, y + 0.5, marker='o', color=path_color)
        if start_pos:
            ax.plot(start_pos[0]+0.5, start_pos[1]+0.5, marker='o', color='green', markersize=10, label='Start')

        # Graficar el punto final con una cruz
        if end_pos:
            ax.plot(end_pos[0]+0.5, end_pos[1]+0.5, marker='x', color='red', markersize=10, label='End')


        
                # Guardar la figura como imagen
        if picker_id<2:
            plt.title(f'picker_{picker_id}_path_{self.cuenta[picker_id]}')
            image_path = f"plots/picker_{picker_id}_path_{self.cuenta[picker_id]}.png"
        else:
            plt.title(F'AMR_{picker_id}_path_{self.cuenta[picker_id]}')
            image_path = f"plots/AMR_{picker_id}_path_{self.cuenta[picker_id]}.png"
        #plt.show()
        
        # Ejemplo de uso

        save_figure(image_path, fig)
                
        #plt.savefig(image_path)  # Guardar la figura en un archivo PNG
        #plt.close(fig)  # Cerrar la figura para liberar recursos
    def plot_warehouse_clusters(self, clusters):
        grid = np.array(self.grid)
        fig, ax = plt.subplots(figsize=(12, 8))

        # Colores suaves para el warehouse
        cmap = plt.cm.Pastel2  # Cambia a una paleta de colores suaves
        ax.imshow(self.grid, cmap=cmap, extent=[0, grid.shape[1], grid.shape[0], 0], interpolation='nearest')

        # Dibujar puntos de I/O si están disponibles
        if hasattr(self, 'io_positions') and self.io_positions:
            for io_point in self.io_positions:
                x, y = io_point
                ax.plot(
                    x + 0.5, y + 0.5,  # Centrar el marcador en la celda
                    marker='s', color='black', markersize=12, label='I/O Point'
                )

        # Configuración de colores para las clases de inventario
        class_colors = {
            'A': 'lightgoldenrodyellow',
            'B': 'lightsteelblue',
            'C': 'lightcoral'
        }

        # Dibujar inventario
        if self.inventory:
            for item in self.inventory:
                x = item.location[0].get_location_x()
                y = item.location[0].get_location_y()
                ax.add_patch(plt.Rectangle((x, y), 1, 1, color=class_colors[item.inv_class]))

        # Configuración de la cuadrícula
        ax.set_xticks(np.arange(0, grid.shape[1], step=self.module_width))
        ax.set_yticks(np.arange(0, grid.shape[0], step=self.cross_aisle_width))
        ax.grid(color='lightgrey', linestyle='--', linewidth=0.5)

        # Dibujar clusters si están disponibles
        if clusters:
            cluster_colors = ['red', 'blue', 'green', 'purple', 'orange']
            for cluster_id, cluster_points in enumerate(clusters):
                cluster_color = cluster_colors[cluster_id % len(cluster_colors)]
                for center in cluster_points:
                    x, y = center
                    ax.scatter(y + 0.5, x + 0.5, color=cluster_color, edgecolor='black', label=f'Cluster {cluster_id + 1}')

        # Leyenda personalizada
        handles = [
            plt.Line2D([0], [0], marker='s', color='w', markerfacecolor='honeydew', markersize=10, label='Charging Station'),
            plt.Line2D([0], [0], marker='s', color='w', markerfacecolor='black', markersize=10, label='I/O Point')
        ]

        # Agregar manejadores para clases de inventario
        for class_type, color in class_colors.items():
            handles.append(plt.Line2D([0], [0], marker='s', color='w', markerfacecolor=color, markersize=10, label=f'Class {class_type} Inventory'))

        # Agregar manejadores para clusters
        unique_labels = {f'Order Centers Cluster {i + 1}': cluster_colors[i] for i in range(len(clusters))}
        for label, color in unique_labels.items():
            handles.append(plt.Line2D([0], [0], marker='o', color=color, markersize=10, label=label))

        # Mostrar leyenda consolidada
        ax.legend(handles=handles, loc='upper left')

        # Mostrar el gráfico
        plt.show()


class ItemLocation:
    def __init__(self, item_location_id, aisle, location, picking_location):
        self.item_location_id = item_location_id
        self.location = location
        self.aisle = aisle
        self.picking_location = picking_location
    #to get the differnet coordinates
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

#it represents an item in the inventory, it has id, location , weight and volume
class Item:
    def __init__(self, item_id, location: list[ItemLocation], weight, volume):
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
        try:
            a =  f'Item id: \t{self.item_id}  Location:\tx = {str(self.location[0].get_location_x())}, y = {str(self.location[0].get_location_y())}, z = {str(self.location[0].get_location_z())}  Weight: \t{self.weight}  Volume: \t{self.volume}\n Class; {self.inv_class}'
        except: 
            a =  f'Item id: \t{self.item_id}  Location:\tx = {str(self.location[0].get_location_x())}, y = {str(self.location[0].get_location_y())}, z = {str(self.location[0].get_location_z())}  Weight: \t{self.weight}  Volume: \t{self.volume}'
        return a

#and OrderItem, its parent class is item, so it has all the attributes
#it represents an item that is ordered
class OrderItem(Item):
    def __init__(self, item_id, location: list[ItemLocation], weight, volume, quantity):
        super().__init__(item_id, location, weight, volume)
        self.quantity = quantity
        self.order_id = None
    
    def add_order_id(self, order_id):
        self.order_id = order_id


    def __repr__(self):
        try:
            return f'\nItem id: {self.item_id:>4}  Location:x = {str(self.location[0].get_location_x()):>2}| y = {str(self.location[0].get_location_y()):>2}| z = {str(self.location[0].get_location_z()):>2}  Weight: {self.weight:>4}  Volume: {self.volume:>4}  Quantity: {self.quantity:>2}, Order: {self.order_id}' 
        except:
            return f'\nItem id: {self.item_id:>4}  Location:x = {str(self.location[0].get_location_x()):>2}| y = {str(self.location[0].get_location_y()):>2}| z = {str(self.location[0].get_location_z()):>2}  Weight: {self.weight:>4}  Volume: {self.volume:>4}  Quantity: {self.quantity:>2}, Order: ' 

#it organizes the articles based on A, B and C classes and its probabilities
class ItemDataset:
    def __init__(self, warehouse, a=.2, b=.3, c=.5):
        #it has a warehouse attached
        self.warehouse = warehouse
        self.a = a
        self.b = b
        self.c = c
        #list that saves the different articles in the different classes
        self.classa = []
        self.classb = []
        self.classc = []
        self._gen_group()

    def _gen_group(self):
        #ir gets all the items in the inventory
        inv = self.warehouse.inventory
        n = len(inv)
        #it classifies them according the class
        self.classa = random.sample(inv, k=int(n * self.a))
        inv = list(set(inv) - set(self.classa))
        self.classb = random.sample(inv, k=int(n * self.b))
        inv = list(set(inv) - set(self.classb))
        self.classc = inv
    def __repr__(self):
        print('CLASS A', len(self.classa))
        print(self.classa)
        print('CLASS B', len(self.classb))
        print(self.classb)
        print('CLASS C',  len(self.classc))
        print(self.classc)

    
#it represents an order, containing different items
class Order:

    def __init__(self, order_id):
        #it has an id, and t also receives the categories previouly generated
        self.order_id = order_id
        #inv_cat it's an object of the class ItemDataset
        o_abc = pickle.load(open('abc_categories.pkl', 'rb'))
        self.inv_cat = o_abc
        #self.order_items = self.order_gen()
        #self.total_weight()
    def total_weight(self):
        return sum(item.weight for item in self.order_items)
    def get_item_ids(self):
        """
        Devuelve una lista de item_id de todos los artículos en la orden.
        """
        return [item.item_id for item in self.order_items]

    def order_gen(self):
        order_items = []
        #an order can have between 1 and 6 articles, with more probability of having 4-6 
        n_order_lines_prob = [1,2,3,4,4,5,5,6,6]
        #elige random el numero de items que tendra la orden
        n_items = random.choice(n_order_lines_prob)
        i = 0
        while i < n_items:
            item = random.choices([random.choice(self.inv_cat.classa), random.choice(self.inv_cat.classb),
                                   random.choice(self.inv_cat.classc)], weights=[0.7, 0.2, 0.1])[0]
            #it generates an item among the possible classes
            #if the item is already in the order it's omitted (to avoid duplicates)
            if order_items and any(it.item_id == item.item_id for it in order_items):
                pass
            else:
                #number of pieces per item is random with the probabilities given
                quant = random.choice([1, 1, 2, 3])
                #for each item generetas the order item respecitely
                order_item = OrderItem(item_id=item.item_id, location=item.location, weight=item.weight, volume=item.volume, quantity=quant)
                #add to the order
                order_items.append(order_item)
                i += 1
        return order_items

    def get_sorted_order(self):
        #it sorts the items given first the aisle, then the y location, adn finally for the location x
        sorted_order = sorted(self.order_items, key=lambda item: (
        item.location[0].aisle, item.location[0].get_location_y(), item.location[0].get_location_x()))
        self.order_items = sorted_order
        #returns an sorted order, does not modify actual
        return self

    #used for return picking policy
    def get_sorted_order_return(self):
        self.order_items = self.get_sorted_order_return_logic()
        return self     

    def get_sorted_order_return_logic(self):
        #it sorts the items given first the aisle, then the x location, and finally for the location y
        #then we invert the orders of items that are on the right aisle of each rack
        #as so we can implement the return policy because the path calculation will follow the order of the items in each order
        sorted_order : list[OrderItem] = sorted(self.order_items, key=lambda item: (
        item.location[0].aisle, item.location[0].get_location_x(), item.location[0].get_location_y()))
        #now i'm inverting the position of all the orders in the right aisle 
        #in order to get the natural order of items for the return path inside the rack
        for i in range(4, 25, 5):
            #retrieves one aisle (to be inverted) at the time and inverts it
            inverted_aisle = [order for order in sorted_order if order.location[0].get_location_x() == i][::-1]
            #if we actually have some elements in that aisle, 
            #substitute the subarray of OrderItem with the inverted array
            if inverted_aisle.count != 0:
                for id_x, orderItem in enumerate(sorted_order):
                    if orderItem.location[0].get_location_x() == i:
                        sorted_order[id_x : (id_x + len(inverted_aisle))] = inverted_aisle
                        break
        return sorted_order

    def get_sorted_order_return_reverse(self):
        sorted_reverse = self.get_sorted_order_return_logic()[::-1]
        self.order_items = sorted_reverse
        return self

    def get_sorted_order_traversal(self):
        #it sorts the items given first the aisle, then the y location, adn finally for the location x
        #then we invert the orders of items each time we change rack
        #as so we can implement the traversal policy because the path calculation will follow the order of the items in each order
        
        sorted_order : list[OrderItem] = sorted(self.order_items, key=lambda item: (
        item.location[0].aisle, item.location[0].get_location_y(), item.location[0].get_location_x()))
        #now i'm inverting the position of all the orders in the right aisle 
        #in order to get the natural order of items for the return path inside the rack
        aisles = []
        #tracks which aisle are we analysing 
        i = 0
        aisles.append(sorted_order[0].location[0].aisle)
        for iter in range(len(sorted_order)):
            #if we are in the next rack 
            if sorted_order[iter].location[0].aisle not in aisles:
                i += 1
                aisles.append(sorted_order[iter].location[0].aisle)
                #if the analysing rack has to be inverted, we inverte it
                if i % 2 == 1:
                    inverted_aisle = [item for item in sorted_order if item.location[0].aisle == aisles[i]][::-1]
                    sorted_order[iter : (iter + len(inverted_aisle))] = inverted_aisle
                    #increment the iter to reach the next element out of the analysing aisle
                    iter = iter + len(inverted_aisle) - 1
        #save the changes
        self.order_items = sorted_order
        return self   

    def set_sorted_order(self):
        #this rewrites the order
        self.order_items = sorted(self.order_items, key=lambda item: (
        item.location[0].aisle, item.location[0].get_location_y(), item.location[0].get_location_x()))

    def order_pop(self, index=0):
        #it allows to take out an item 
        item = self.order_items.pop(index)
        return item

    def __repr__(self):
        order_ls = ""
        for item in self.order_items:
            order_ls += f"{item}\n" + "-" * 100 + "\n"
        return f'\nOrder id: {self.order_id}\n{"-" * 100}\nOrder items: \n\n{order_ls}'

class OrderBatch(Order):
    def __init__(self, order_batch_id, orders):
        super().__init__(order_batch_id)
        #orders is a list of instance of the class order
        #id is the batch id
        self.id = order_batch_id
        #print(self.id)
        self.orders = self.add_orders(orders)
        #print(self.orders)
        #print(self.orders)
        self.consolidated_items = self.consolidate_items()
        self.consolidated_items = self.sort_items_by_location()
        self.order_items = self.consolidated_items

    def add_orders(self, orders):
        #we save the orders with their ids to be able to referentiate to them easily 
        #order_dict is a dictionary that saves each order with their respective id
        order_dict = {}
        for order in orders:
            order_dict[order.order_id] = order
            for item in order.order_items:
                item.add_order_id(order.order_id)
        return order_dict

    def consolidate_items(self):
        #we put all the items of the batch in the same list
        consolidated_items = []
        for order in self.orders.values():
            for item in order.order_items :
                consolidated_items.append(item) 
        
        return consolidated_items

    def sort_items_by_location(self):
        #it sorts the items given first the aisle, then the y location, adn finally for the location x
        sorted_batch = sorted(self.consolidated_items, key=lambda item: (
        item.location[0].aisle, item.location[0].get_location_y(), item.location[0].get_location_x()))
        #print(f'***************{self.id}*****************************')
        #print(sorted_batch)
        return sorted_batch
    def __repr__(self):
        order_ls = ""
        for item in self.order_items:
            order_ls += f"{item}\n" + "-" * 100 + "\n"
        return f'\nBatch id: {self.order_id}\n{"-" * 100}\n items: \n\n{order_ls}'



##############################
# AGENTS #####################
##############################

class Picker(mesa.Agent):
    def __init__(self, picker_id, model, current_position, routing_policy,preference, speed=0.95, pref_batch=False,linked_amr=None,
                 next_action="wait", path=[]):
        super().__init__(picker_id, model)
        #current position
        self.current_pos = current_position[0]
        #speed set
        self.speed = speed
        #item that it's holding
        self.item = None
        #order that it's taking care of
        self.order = None
        #amr linked to him
        self.linked_amr = linked_amr
        #next action to do
        self.next_action = next_action
        #list of following actions
        self.next_actions = [self.next_action]
        #path determined to follow
        self.path = path
        self.pref_batch = pref_batch

        self.distance_walked = 0
        self.routing_policy = routing_policy
        self.preference = preference
        self.satisfaction = 0       #ADDED
        self.num_order = 0          #ADDED
        self.num_sat_order = 0      #ADDED

        #self.relat_satisfaction = self.num_sat_order/self.num_order   #ADDED
        

    def compute_path(self, current_position, final_position):
        #to understand the input let's look into when the function is called in step method
        #e.g self.path = self.compute_path(self.current_pos, self.item.location[0].picking_location)
        #it's giving the current location of the picker, and it's calling the item location of the item assingned
        #registrate the position that the robot is currently
        current_pos = current_position
        #create a list to save the path
        path = []
        #recover the width of the module 
        module_width = self.model.warehouse.module_width
        #current_pos[0] ([0] to access the first  coordinate) // module_width would be the module that it th picker is in (e.g the aisle)
        #final_position[0] (the coordinate) // module_width would be the module that it th item is in (e.g the aisle)
        #if they are the same (Meaning the item and the picker are in the same aisle) or if the current position is the origin ( list(current_pos) == [0, 0])
        if current_pos[0] // module_width == final_position[0] // module_width or tuple(current_pos) in self.model.warehouse.io_positions:
            #calculate the direction in x in which the picker must move (increment x)
            # if the item is a position with a higher number, then the picker must move positive in the x axis
            #the other option, the picker has to move on the negative direction in the x. (it's like identifying is the picker must go backward or forwards in the module width)
            increment_x = -1 if final_position[0] <= current_pos[0] else 1
            #the picker moves step by step until it reaches the final position
            for x in range(current_pos[0], final_position[0], increment_x):
                path.append([x + increment_x, current_pos[1]])
            
            #it verifies that the list path is not empty, and in the case, assigs as the position, the position reached by the movement in the x axis
            if path: current_pos = path[-1]
            #the same for the y axis, moving backwards or forwards in the same aisles until it reaches the position
            increment_y = -1 if final_position[1] <= current_pos[1] else 1
            for y in range(current_pos[1], final_position[1], increment_y):
                path.append([current_pos[0], y + increment_y])
                self.distance_walked+=1
        
        #f the item is not in the same aisle than the picker
        elif current_pos[0] // module_width != final_position[0] // module_width:
            #the warehouse has a cross aisle that allows the picker to change modules, so the picker must reach the position of the cross aisle first
            #determine if the picker should take the way up or down, when entering the next aisle according the distance from the actual position (in the y sense) 
            if self.routing_policy == 'return':
                entry = "upper"
            else:
                lower_y_limit = self.model.warehouse.length
                entry = "upper" if final_position[1] + current_pos[1] <= lower_y_limit - final_position[1] + lower_y_limit - \
                                current_pos[1] else "lower"
                #same comparison as above, seiing if the picker has to move on the widht of the aisle in which direction
                #and move him until it reaches the chosen exit of the aisle

            increment_x = -1 if final_position[0] <= current_pos[0] else 1
            #and move him until it reaches the chosen entry of the destination aisle, moving in it in the - direction in the y axis
            
            if entry == "upper" and current_pos[1] not in [0, 1]:
                #in this case is either if it has to go to the origin (final_position = 0) or if the chosen entry is in the upper part. 
                top_limit = 1 if final_position[1] == 0 else self.model.warehouse.cross_aisle_width
                #this is vertical movement to go out of the aisle
                for y in range(current_pos[1], top_limit - 1, -1):
                    path.append([current_pos[0], y - 1])
                    self.distance_walked+=1
                current_pos = path[-1]
                #after reaching the top limit, the picker moves in the x axis until it reaches the x of the aisle it needs to access
                for x in range(current_pos[0], final_position[0], increment_x):
                    path.append([x + increment_x, current_pos[1]])
                    self.distance_walked+=1
                
                current_pos = path[-1]
                #then it moves along the aisle until it reaches the position of the item in the aisle
                for y in range(current_pos[1], final_position[1]):
                    path.append([current_pos[0], y + 1])
                    self.distance_walked+=1
           
            #this is in the case the picker it's not properly on the aisle
            # print(current_pos)
            # print(final_position)
           
            if entry == "upper" and current_pos[1] in [0, 1]:
            
                top_limit = self.model.warehouse.cross_aisle_width
                #this is vertical movement to go out of the aisle
                #the rest is the same as above
                
                for y in range(current_pos[1], top_limit-1,1):
                    path.append([current_pos[0], y+1])
                    self.distance_walked+=1
                current_pos = path[-1]
                for x in range(current_pos[0], final_position[0], increment_x):
                    path.append([x + increment_x, current_pos[1]])
                    self.distance_walked+=1
                current_pos = path[-1]
                for y in range(current_pos[1], final_position[1]):
                    path.append([current_pos[0], y + 1])
                    self.distance_walked+=1
            
            #in the case that the closer exit is in the lower part of the aisle
            elif entry == "lower":
                #it moves to to the center aisle to get him out of the aile he's in
                for y in range(current_pos[1],self.model.warehouse.cross_aisle_width + self.model.warehouse.aisle_length):
                    path.append([current_pos[0], y + 1])
                    self.distance_walked+=1
                current_pos = path[-1]
                #it moves him until it reaches the aisle
                for x in range(current_pos[0], final_position[0], increment_x):
                    path.append([x + increment_x, current_pos[1]])
                    self.distance_walked+=1
                current_pos = path[-1]
                #then when it reaches the destination aisle it moves him down 
                for y in range(current_pos[1], final_position[1], -1):
                    path.append([current_pos[0], y - 1])
                    self.distance_walked+=1
        # if self.model.warehouse.graph:
        #     self.model.warehouse.plot_warehouse(path, self.unique_id, current_position, final_position)
        return path

    def step(self):
        #in every step of the simulation, it does the next action in the lsit
        self.next_action = self.next_actions.pop(0)
        #if it the instruction is to wait
        if self.next_action == "wait":
            #if there are orders, and it has an amr linked
            if self.model.orders and self.model.available_amr:
                #it gets the following order
                #it links the amr to the picker
                self.linked_amr = self.model.available_amr.pop(0)
                #It gives the next order based on criteria for assignment
                self.order = self.model.assign_order(self)
                
                if self.order == None:
                    self.next_actions += ["wait"]
                    #it it does not have any order to give, waits, and unlinks the amr
                    self.model.available_amr.append(self.linked_amr)
                    self.linked_amr = None
                else:
                    #gets the item in the order
                    self.item = self.order.order_pop(0)
                    #it gets the path to follow
                    self.path = self.compute_path(self.current_pos, self.item.location[0].picking_location)
                    
                    self.linked_amr.linked_picker = self
                    #it tells the amr to register the path
                    self.linked_amr.next_action = "path"
                    #if the path has movements to do, keep telling him to move, as the number of positions in the path
                    if self.path:
                        self.next_actions += ["move"] * len(self.path)
                    else:
                        #if it reached the position (path is empty), tell him to pick
                        self.next_actions += ["pick"] * sum(random.choice([1, 2]) for _ in range(self.item.quantity))
                        self.next_actions += ["unload"]
            #if there arent orders
            else:
                self.next_actions += ["wait"]
        #if the action is to move
        elif self.next_action == "move":
            #if the path it has movements
            if self.path:
                #speed is random 
                if random.choices([True, False], [self.speed, 1 - self.speed])[0]:
                    self.current_pos = self.path.pop(0)
                else:
                    self.next_actions.insert(0, "move")
            if not (self.path):
                #if the path is finis, pick, the picking time is random choice between (1 and 2)
                self.next_actions += ["pick"] * sum(random.choice([1, 2]) for _ in range(self.item.quantity))
                self.next_actions += ["unload"]
        elif self.next_action == "pick":
            #if the action it's pick then it just do the action (takes the time)
            #from previously it's given than after finishing picking there's unload
            pass
        elif self.next_action == "unload":
            #if the following action is to unload, check for the robot
            is_robot_ready = self.linked_amr.next_action == "load"
            #if it0s ready
            if is_robot_ready:
                #give the item to the robot
                self.linked_amr.load_amr(self.item, self.item.order_id)
                #take the item away from picker
                self.item = None
                #if there are more iems to pick
                if self.order.order_items:
                    #assining the item to pick
                    self.item = self.order.order_pop(0)
                    #if the item is in the location that the picker i's in , give him the action to pick and then unload
                    if self.item.location[0].picking_location[:2] == self.current_pos:
                        self.next_actions += ["pick"] * sum(
                            random.choice([1, 2]) for _ in range(self.item.quantity)) + ["unload"]
                    else:
                        #if not calculate the path
                        self.path = self.compute_path(self.current_pos, self.item.location[0].picking_location)
                        self.next_actions += ["move"] * len(self.path)
                else:
                    #if there are not more items in the order
                    self.next_actions += ["wait"]
            #if the robot is not ready postpone the unloading to the next time
            elif not(is_robot_ready):
                self.next_actions +=["unload"]



class Amr(mesa.Agent):
    def __init__(self, amr_id, model, current_position, routing_policy, linked_picker=None, next_action="wait"):
        super().__init__(amr_id, model)
        #position
        self.current_pos = current_position[0]
        #which is the picker linked
        self.linked_picker = linked_picker
        #items carried
        self.carried_items = defaultdict(list)
        #following actions
        self.next_action = next_action
        #Path to follow
        self.path = []
        #number of orders it can carry
        self.capacity = 4
        self.routing_policy = routing_policy

    def load_amr(self, item: OrderItem, order_id):
        #add and item to the carried items
        self.carried_items[order_id].append(item)

    def compute_path(self, current_position, final_position):
        current_pos = current_position
        path = []
        #same as picker
        module_width = self.model.warehouse.module_width
        if current_pos[0] // module_width == final_position[0] // module_width or tuple(current_pos) in self.model.warehouse.io_positions:
            increment_x = -1 if final_position[0] <= current_pos[0] else 1
            for x in range(current_pos[0], final_position[0], increment_x):
                path.append([x + increment_x, current_pos[1]])
            if path: current_pos = path[-1]
            increment_y = -1 if final_position[1] <= current_pos[1] else 1
            for y in range(current_pos[1], final_position[1], increment_y):
                path.append([current_pos[0], y + increment_y])
        elif current_pos[0] // module_width != final_position[0] // module_width:
            if self.routing_policy == 'return':
                entry = "upper"
            else:           
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
                for y in range(current_pos[1], top_limit - 1, 1):
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
        # if self.model.warehouse.graph:
        #     self.model.warehouse.plot_warehouse(path, self.unique_id, current_position, final_position)
        return path

    def compute_path_return(self, current_position, final_positions):
        current_pos = current_position
        path = []
        final_pos = final_positions[0] if len(final_positions) == 1 else (current_pos[0], 0)
        for y in range(current_pos[1], final_pos[1], -1):
            path.append([current_pos[0], y-1])
        current_pos = path[-1]
        for x in range(current_pos[0],final_pos[0], -1):
            path.append([x-1, current_pos[1]])
        # if self.model.warehouse.graph:
        #     self.model.warehouse.plot_warehouse(path, self.unique_id, current_position, final_pos)
        return path

    def step(self):
        #si debe esperar espera
        if self.next_action == "wait":
            pass
        #must register a path
        elif self.next_action == "path":
            #calculate the path
            self.path = self.compute_path(self.current_pos, self.linked_picker.item.location[0].picking_location)
            #
            self.next_action = "move"
        #if it must move
        elif self.next_action == "move":
            #it moves him stem by step in one position
            self.current_pos = self.path.pop(0)
            #if there are not more steps to do, it tell hi to load the item
            if not self.path:
                self.next_action = "load"
        #If the action is to lad
        elif self.next_action == "load":
            #if the followign action of the picker is to wait (because it put the item into the amr, and then it's told to wait if there are not more items)
            if self.linked_picker.next_actions[0] == "wait":
                #unlink them
                self.linked_picker.linked_amr = None
                self.linked_picker = None
                #return
                self.next_action = "return"
                #return
                self.path = self.compute_path_return(self.current_pos, self.model.warehouse.io_positions)
            else:
                #go to the next item in the order
                self.path = self.compute_path(self.current_pos, self.linked_picker.item.location[0].picking_location)
                if self.path:
                    self.next_action = "move"
                else:
                    self.next_action = "load"
        #if following action is to return do the path to return
        elif self.next_action == "return":
            self.current_pos = self.path.pop(0)
            if not (self.path):
                #if it reached the destination, unload
                self.next_action = "unload"
        #If it has to unload, empyhe carry items and tell him to wait, and make him self available
        elif self.next_action == "unload":
            
            primera_clave = next(iter(self.carried_items))  # Obtiene la primera clave
            del self.carried_items[primera_clave]  #elimina el primer elemento disponible
            #if there are more items
            if len(self.carried_items)>0:
                self.next_action = "unload"
            else:

                self.next_action = "wait"
                self.model.available_amr.append(self)



##############################
# MODEL ######################
##############################

class WarehouseModel(mesa.Model):
    def __init__(self, warehouse, n_pickers, n_amr, orders, batching, batching_method, batch_size, routing_policy, assignation_method):
        super().__init__()
        self.warehouse = warehouse
        self.n_pickers = n_pickers
        self.n_amr = n_amr
        self.available_amr = []
        self.assignation_method = assignation_method
        self.schedule = mesa.time.BaseScheduler(self)
        self.batch_size = batch_size
        self.routing_policy = routing_policy
        orders = self.get_orders(orders, batching, batching_method)
        
        self.orders = []
        self.distances = []
        if assignation_method == 'productivity':
            for order in orders:
                #print(order)
                items_ordenada = self.insertion_items_with_return((0,0), order)
                order.order_items = items_ordenada
                self.orders.append(order)
        else:
            self.orders = orders
                
        self.pickers = [] 
        preferences = ['weight', 'distance']
        for picker_id in range(self.n_pickers):
            picker = Picker(picker_id=picker_id, model=self, current_position=self.warehouse.io_positions, preference=preferences.pop(0), routing_policy=self.routing_policy)
            self.pickers.append(picker)
            self.schedule.add(picker)
        # self.warehouse.plot_warehouse([], 0, self.warehouse.io_positions[0], self.warehouse.charge_pos)
        #print(self.orders)
        
        #picker and amr start at the io point


        for amr_id in range(self.n_amr):
            
            amr = Amr(amr_id=n_pickers + amr_id, model=self, current_position=self.warehouse.io_positions, routing_policy=self.routing_policy)
            self.available_amr.append(amr)
            self.schedule.add(amr)
        if self.assignation_method=='productivity':
            self.orders_for_pickers = self.clusters_and_assign_orders()

    def insertion_items_with_return(self, io_point, order):
        """
        Arranges the items in an order using the insertion heuristic. Calculates the total distance using path distance
        between item locations and includes the return to the I/O point after the last item is picked.
        """
        # Start the route with the closest item to the I/O point
        route = [order.order_items.pop(0)]  
        total_distance = 0

        # Function to calculate the Manhattan distance between two points
        def calculate_manhattan_distance(p1, p2):
            return abs(p1.get_location_x() - p2.get_location_x()) + abs(p1.get_location_y() - p2.get_location_y())

        # Initial position is the first item in the route
        first_item_position = route[0].location[0]
        # Initial distance from I/O point to the first item
        total_distance += distance_compute_path((first_item_position.get_location_x(), first_item_position.get_location_y()), (io_point[0], io_point[1]))
        #total_distance += abs(first_item_position.get_location_x() - io_point[0]) + abs(first_item_position.get_location_y() - io_point[1])

        # While there are items remaining in the order
        while order.order_items:
            best_distance = float('inf')
            best_item = None
            best_position = -1

            # Iterate through all items to find the best insertion position in the route
            for i in range(len(order.order_items)):
                item = order.order_items[i]
                # Calculate the insertion distance between each item and the current route
                for j in range(len(route)):
                    '''
                    dist = calculate_manhattan_distance(
                        route[j].location[0],
                        item.location[0]
                    )
                    '''
                    dist = distance_compute_path((route[j].location[0].get_location_x(), route[j].location[0].get_location_y()),
                                                  (item.location[0].get_location_x(), item.location[0].get_location_y()))

                    if dist < best_distance:
                        best_distance = dist
                        best_item = item
                        best_position = j

            # Remove the best item from the list of items
            order.order_items.remove(best_item)

            # Insert the best item at the optimal position in the route
            route.insert(best_position, best_item)
            total_distance += best_distance

        # After adding all items, calculate the return distance to the I/O point
        last_item_position = route[-1].location[0]
        #return_distance = abs(last_item_position.get_location_x() - io_point[0]) + abs(last_item_position.get_location_y() - io_point[1])
        return_distance = distance_compute_path((last_item_position.get_location_x(), last_item_position.get_location_y()), io_point)
        total_distance += return_distance

        return route
    def insertion_orders_with_optimal_return(self, orders, io_point):
        """
        Inserts orders in a picking sequence using the insertion heuristic,
        utilizing path distance between item locations and considering the return to the I/O point
        optimally at the end of each order.
        """
        # Initialize the route with the first order closest to the I/O point
        route = [orders.pop(0)]  # Start with the first order
        print(route)
        total_distance = 0

        # Function to calculate Manhattan distance between two points (x, y, z)
        def calculate_manhattan_distance(p1, p2):
            return abs(p1.get_location_x() - p2.get_location_x()) + abs(p1.get_location_y() - p2.get_location_y())

        # Function to calculate the return distance to the I/O point after an order
        def calculate_return_distance(route, io_point):
            p1 = route[-1].order_items[0].location[0]
            return abs(p1.get_location_x() - io_point[0]) + abs(p1.get_location_y() - io_point[1])

        # While there are orders to assign
        while orders:
            best_distance = float('inf')
            best_order = None
            best_position = -1

            # Iterate over all orders and find the best position to insert them
            for i in range(len(orders)):
                order = orders[i]
                # Calculate the insertion distance between each order and the current route
                for j in range(len(route)):
                    '''
                    dist = calculate_manhattan_distance(
                        route[j].order_items[0].location[0],
                        order.order_items[0].location[0]
                    )
                    '''
                    last_item_location = route[j].order_items[-1].location[0]  # Último ítem de la ruta
                    first_order_location = order.order_items[0].location[0]  # Primer ítem de la orden evaluada

                    # Calcular la distancia entre el último ítem de la ruta y el primer ítem de la orden evaluada
                    dist = distance_compute_path(
                        (last_item_location.get_location_x(), last_item_location.get_location_y()),
                        (first_order_location.get_location_x(), first_order_location.get_location_y()))

                    if dist < best_distance:
                        best_distance = dist
                        best_order = order
                        best_position = j

            # Remove the best order from the list of orders
            orders.remove(best_order)

            # Insert the best order in the route at the found position
            route.insert(best_position, best_order)
            total_distance += best_distance

            # After adding the order, calculate the return distance to the I/O point
            return_distance = calculate_return_distance(route, io_point)
            total_distance += return_distance

        return route

    def clusters_and_assign_orders(self):
        num_clusters = 2  # Number of clusters to create (can be adjusted)
        order_centers = []
        orders = []
        order_center_plot = []
        # Get the center of each order (average of item positions)
        for order in self.orders:
            coords = np.array([[item.location[0].get_location_x(), 
                                item.location[0].get_location_y()] for item in order.order_items])
            coords_inv = np.array([[item.location[0].get_location_y(), 
                                item.location[0].get_location_x()] for item in order.order_items])
            order_center_plot.append(coords_inv.mean(axis = 0))
            center = coords.mean(axis=0)
            order_centers.append(center)
            orders.append(order)

        # Convert the order centers into a numpy matrix
        order_centers = np.array(order_centers)

        # Scale the coordinates before clustering
        scaler = StandardScaler()
        order_centers_scaled = scaler.fit_transform(order_centers)

        # Apply KMedoids to generate clusters of orders using Manhattan distance
        kmedoids = KMedoids(n_clusters=num_clusters, metric='manhattan') # type: ignore
        kmedoids.fit(order_centers_scaled)
        labels = kmedoids.labels_
        
        # Create a list of clusters, where each cluster contains the orders assigned to that cluster
        clusters = [[] for _ in range(num_clusters)]
        clusters_pos = [[]for _ in range(num_clusters)]
        for label, order in zip(labels, orders):
            clusters[label].append(order)
        clusters_pos = [[] for _ in range(num_clusters)]
        for label, center in zip(labels, order_center_plot):  # Usar order_centers para posiciones
            clusters_pos[label].append(center)
        # Crear el gráfico

        #self.warehouse.plot_warehouse_clusters(clusters_pos)
        
        total_items = 0
        for cluster_id, cluster in enumerate(clusters):
            print(f'Number of orders in Cluster {cluster_id + 1}: {len(cluster)}')
            print(f'Number of items in Cluster {cluster_id + 1}: {sum(len(order.order_items) for order in cluster)}')
            total_items += sum(len(order.order_items) for order in cluster)
        
        # Assign items per picker
        items_per_picker = total_items // 2

        # Sort clusters by size (number of orders in each one)
        smaller_cluster_id, smaller_cluster = min(enumerate(clusters), key=lambda x: len(x[1]))
        bigger_cluster_id, bigger_cluster = max((i, cluster) for i, cluster in enumerate(clusters) if i != smaller_cluster_id)

        print(f"Orders in smaller cluster: {len(smaller_cluster)}")
        print(f"Orders in bigger cluster: {len(bigger_cluster)}")
        print(f"Items per picker: {items_per_picker}")
        print(smaller_cluster== bigger_cluster)

        # Initialize a dictionary for the orders assigned to each picker
        picker_orders = {i: [] for i in range(0,2)}  # Assuming 2 pickers

        # Assign all orders from the smaller cluster
        picker_index = 0  # Start with the first picker
        for order in smaller_cluster:
            picker_orders[picker_index].append(order)

        # Balance the number of items
        while sum(len(order.order_items) for order in picker_orders[picker_index]) < items_per_picker:
            # Find the closest order in the bigger cluster
            closest_order = None
            min_distance = float('inf')
            for order in bigger_cluster:
                # Calculate the distance of the order to the cluster center
                coords = np.array([[item.location[0].get_location_x(), 
                                    item.location[0].get_location_y()] for item in order.order_items])
                center = coords.mean(axis=0).tolist()
                
                # Calculate the Manhattan distance
                cluster_center = np.mean([np.array([item.location[0].get_location_x(), 
                                                    item.location[0].get_location_y()]) for item in order.order_items], axis=0).tolist()
                print(center, cluster_center)
                distance = distance_compute_path((int(center[0]), int(center[1])), (int(cluster_center[0]), int(cluster_center[1])))
                #distance = np.abs(center - cluster_center).sum()  # Manhattan distance

                if distance < min_distance:
                    min_distance = distance
                    closest_order = order

            # Assign the closest order to the picker
            picker_orders[picker_index].append(closest_order)
            bigger_cluster.remove(closest_order)

        # Assign the remaining orders to the next picker
        picker_index = 1
        for order in bigger_cluster:
            picker_orders[picker_index].append(order)

        # Display assignment results
        print('PICKER 0')
        print(len(picker_orders[0]), 'orders')
        print(sum(len(order.order_items) for order in picker_orders[0]), 'items')
        
        print('PICKER 1')
        print(len(picker_orders[1]), 'orders')
        print(sum(len(order.order_items) for order in picker_orders[1]), 'items')

        # Plot the assignment of orders and clusters
        fig, ax = plt.subplots(figsize=(10, 7))

        # Plot the centers of clusters (after scaling)
        ax.scatter(order_centers_scaled[:, 0], order_centers_scaled[:, 1], c=labels, cmap='viridis', s=100, label='Order Centers')

        # Color the orders according to the cluster
        for cluster_id, cluster in enumerate(clusters):
            cluster_points = [np.array([item.location[0].get_location_x(), item.location[0].get_location_y()]) for order in cluster for item in order.order_items]
            cluster_points = np.array(cluster_points)

            # Scale the coordinates of orders
            cluster_points_scaled = scaler.transform(cluster_points)

            ax.scatter(cluster_points_scaled[:, 0], cluster_points_scaled[:, 1], c=[cluster_id] * len(cluster_points), cmap='viridis', alpha=0.5)

        # Picker assignment
        picker_colors = ['r', 'b']
        for picker_index, orders in picker_orders.items():
            for order in orders:
                coords = np.array([[item.location[0].get_location_x(), item.location[0].get_location_y()] for item in order.order_items])
                # Scale the coordinates of assigned orders
                coords_scaled = scaler.transform(coords)
                ax.scatter(coords_scaled[:, 0], coords_scaled[:, 1], color=picker_colors[picker_index-1], label=f'Picker {picker_index}', alpha=0.7)

        ax.set_xlabel('X (Position)')
        ax.set_ylabel('Y (Position)')
        ax.set_title('Order Clusters and Picker Assignment')
        ax.legend()
        #plt.show()
        #print(len(picker_orders))
        for i in picker_orders:
            sorted_orders = self.insertion_orders_with_optimal_return(picker_orders[i], (0,0))
            for order in sorted_orders:
                picker_orders[i].append(order)
        return picker_orders
    
    #ADDED
    def assign_order(self, picker : Picker):
        picker_location = picker.current_pos 
        picker.num_order +=1
        #print('num_order', picker.num_order)
        if self.assignation_method == 'ordered':
            return self.orders.pop(0)
        
        elif self.assignation_method == 'productivity':
            #print(picker.unique_id)
            if len(self.orders_for_pickers[picker.unique_id])>0:
                next_order =  self.orders_for_pickers[picker.unique_id].pop(0)
                self.orders.remove(next_order)
                return next_order
            else:
                return None

        #tried to write an amr based method
        # elif self.assignation_method == 'AMR':
        #     ids = {2: 0, 3: 1}
        #     #print(picker.linked_amr.unique_id)
        #     if len(self.orders_for_pickers[ids[picker.linked_amr.unique_id]])>0:
        #         next_order =  self.orders_for_pickers[ids[picker.linked_amr.unique_id]].pop(0)
        #         self.orders.remove(next_order)
        #         return next_order
        #     else:
        #         return None
            
        
        elif self.assignation_method == 'pref_distance':       
            dist_order = min(self.orders,key=lambda x: self.calculate_total_path_distance(order, picker_location))          
            #dist_order = min(self.orders,key=lambda x: self.calculate_total_manhattan_distance(order, picker_location))
            distance = self.calculate_total_path_distance(dist_order, picker_location)
            self.distances.append(distance)
            if distance < 60:      #il picker non vuole percorrere più di 75m per completare un ordine
                picker.satisfaction+=1
                picker.num_sat_order+=1
                if distance < 40:
                    picker.satisfaction +=1
                    if distance < 20:
                        picker.satisfaction +=1
                            
            self.orders.remove(dist_order)
            return dist_order
        
        elif self.assignation_method == 'pref_weight':
            
            lighter_order = min(self.orders,key=lambda x: order.total_weight())            
            weight = lighter_order.total_weight()
            if weight < 5.4*self.batch_size:        
                picker.satisfaction +=1
                picker.num_sat_order +=1
                if weight < 4*self.batch_size:        
                    picker.satisfaction +=1
                    if weight < 2.25*self.batch_size:       
                        picker.satisfaction +=1
            self.orders.remove(lighter_order)
            return lighter_order
        
        elif self.assignation_method == 'pref_I/O':
            closest_order = min(self.orders,key=lambda x: self.calculate_distance_first_item(order,  self.warehouse.io_pos))
            distance = self.calculate_distance_first_item(closest_order, self.warehouse.io_pos)
            if distance < 60:      #il picker non vuole che l'AMR all'I/O percorra più di 25m 
                picker.satisfaction +=1
                picker.num_sat_order +=1
                if distance < 40:
                    picker.satisfaction +=1
                    if distance < 20:
                        picker.satisfaction +=1
            self.orders.remove(closest_order)
            return closest_order
        elif self.assignation_method == 'picker_preference':
            if picker.preference == 'distance':       
                dist_order = min(self.orders,key=lambda x: self.calculate_total_path_distance(order, picker_location))          
                #dist_order = min(self.orders,key=lambda x: self.calculate_total_manhattan_distance(order, picker_location))
                distance = self.calculate_total_path_distance(dist_order, picker_location)
                self.distances.append(distance)
                if distance < 40:      #il picker non vuole percorrere più di 75m per completare un ordine
                    picker.satisfaction+=1
                    picker.num_sat_order+=1
                    if distance < 20:
                        picker.satisfaction +=1
                        if distance < 10:
                            picker.satisfaction +=1
                                
                self.orders.remove(dist_order)
                return dist_order
        
            elif picker.preference == 'weight':
                #('weight')
                
                lighter_order = min(self.orders,key=lambda x: order.total_weight())            
                weight = lighter_order.total_weight()
                #print(weight)
                
                if weight < 5.4*self.batch_size:        
                    picker.satisfaction +=1
                    picker.num_sat_order +=1
                    if weight < 4*self.batch_size:        
                        picker.satisfaction +=1
                        if weight < 2.25*self.batch_size:       
                            picker.satisfaction +=1
                self.orders.remove(lighter_order)
                return lighter_order
            
        elif self.assignation_method == 'return_v2':
            if picker.linked_amr.current_pos[0] < self.warehouse.width/2 : 
                return self.orders.pop(0)
            else:
                return self.orders.pop()

    
    def calculate_average_manhattan_distance(self, order, picker_location):
        distance = 0
        count = 0
        for item in order.order_items:
            distance += abs(item.location[0].get_location_x() - picker_location[0]) + abs(item.location[0].get_location_y() - picker_location[1])
            count += 1
        return distance / count if count > 0 else 0
    def calculate_total_manhattan_distance(self, order, picker_location):
        distance = 0
        count = 0
        primo_item = order.order_items[0]
        distance += abs(primo_item.location[0].get_location_x() - picker_location[0]) + abs(primo_item.location[0].get_location_y() - picker_location[1])
        for i in range(0, len(order.order_items)-1):
            item_0 = order.order_items[i]
            item_1 = order.order_items[i+1]
            distance += abs(item_0.location[0].get_location_x() - item_1.location[0].get_location_x()) + abs(item_0.location[0].get_location_y() - item_0.location[0].get_location_x())
            count += 1
        return distance / count if count > 0 else 0
    
    def calculate_total_path_distance(self, order, picker_location):
        distance = 0
        count = 0
        primo_item = order.order_items[0]
        
        distance = distance_compute_path((primo_item.location[0].get_location_x(), primo_item.location[0].get_location_y()), picker_location)
        for i in range(0, len(order.order_items)-1):
            item_0 = order.order_items[i]
            item_1 = order.order_items[i+1]
            distance += distance_compute_path((item_0.location[0].get_location_x(), item_0.location[0].get_location_y()),(item_1.location[0].get_location_x(), item_1.location[0].get_location_y()) )
            count += 1
        return distance / count if count > 0 else 0
  

    def calculate_distance_first_item(self, order, location):
        item1 = order.order_items[0]
        distance_path = distance_compute_path((item1.location[0].get_location_x(), item1.location[0].get_location_y()),(location))
        distance_manhattan = abs(item1.location[0].get_location_x() - location[0]) + abs(item1.location[0].get_location_y() - location[1])
        return distance_path
           
    def get_orders(self, orders, batching, method):
        
        if not batching:
            for order in orders:
                for item in order.order_items:
                    item.add_order_id(order.order_id)
            if self.routing_policy == 'return':
                return [order.get_sorted_order_return() for order in orders]
            elif self.routing_policy == 'traversal':
                return [order.get_sorted_order_traversal() for order in orders]
            elif self.routing_policy == 'return_v2':
                ordersToReturn = []
                size = len(orders)
                ordersToReturn += [order.get_sorted_order_return() for order in orders[0 : int(size/2)]]
                ordersToReturn += [order.get_sorted_order_return_reverse() for order in orders[int(size/2) : size]]
                return ordersToReturn
            else:
                return [order.get_sorted_order() for order in orders]

        else:
            lista_batches = []
            batches_obj = Batch(orders, method, self.batch_size) #we create the batch depending on the method
            batches = batches_obj.batches #we recover the list of batches
            
            id = 0
            for bat in batches:
                # print(id)
                # print(bat)
                order_batch= OrderBatch(id, bat) #we convert the batch into an 'order'
                if self.routing_policy == 'return':
                    order_batch.get_sorted_order_return()  
                elif self.routing_policy == 'traversal':
                    order_batch.get_sorted_order_traversal()
                elif self.routing_policy == 'return_v2':
                    if id < int(len(batches)/2):
                        order_batch.get_sorted_order_return()
                    else:
                        order_batch.get_sorted_order_return_reverse()               
                lista_batches.append(order_batch)
                # print(order_batch)
                id+=1
            print('the number of batches is', len(batches))
            print('the number of orders in each bach is', [len(orders) for orders in batches])

            return lista_batches

    def step(self):
        self.schedule.step()


#Greedy Heuristic
#Il metodo Greedy Heuristic parte anch'esso da un singolo ordine ma, diversamente dal Nearest Neighbor, non si concentra solo sul più vicino al seed. 
#Al contrario, in ogni iterazione, valuta tutti gli ordini disponibili, scegliendo quello che massimizza o minimizza un obiettivo globale (es. minimizzare il peso totale del batch).

class Batch:
    def __init__(self, orders_list, method, batch_size):
        self.orders_list = orders_list
        self.batches = []
        self.batch_size = batch_size
        if method == 'weight':
            self.create_batches_by_weight()
        if method == 'items':
            self.create_batches_by_common_items()
        if method == 'distance':
            self.create_batches_by_distance()
        if method == 'default':
            self.create_batches_by_default()
       
    def calculate_common_items(self, batch):
        """
        Calcola il numero di item_id in comune per un batch di 4 ordini.
        """
        # Usa il primo ordine del batch per iniziare l'intersezione
        common_item_ids = set(batch[0].get_item_ids())
        
        # Intersezione con gli item_id degli altri ordini nel batch
        for order in batch[1:]:
            common_item_ids.intersection_update(set(order.get_item_ids()))
        
        # Restituisce il numero di item_id comuni
        return len(common_item_ids)
    
    def calculate_average_manhattan_distance(self, order1, order2):
        """
        Calcola la distanza media di Manhattan tra tutti gli item di due ordini.
        """
        distance = 0
        count = 0
        for item1 in order1.order_items:
            for item2 in order2.order_items:
                distance += abs(item1.location[0].get_location_x() - item2.location[0].get_location_x()) + abs(item1.location[0].get_location_y() - item2.location[0].get_location_y())
                count += 1
        return distance / count if count > 0 else 0
    
    def create_batches_by_common_items(self):
        """
        Crea batch di 4 ordini ottimizzando il numero di item_id in comune.
        """
        orders = set(self.orders_list)  # Usa un set per tenere traccia degli ordini non ancora assegnati
        while len(orders) >= self.batch_size:
            batch = []
            # Seleziona un ordine iniziale casuale
            order = orders.pop()
            batch.append(order)

            # Seleziona gli ordini con il massimo numero di item comuni
            for _ in range(self.batch_size-1):
                next_order = max(
                    orders,
                    key=lambda x: len(set(order.get_item_ids()).intersection(set(x.get_item_ids()))),
                )
                batch.append(next_order)
                orders.remove(next_order)

            self.batches.append(batch)

    def create_batches_by_distance(self):
        """
        Crea batch di 4 ordini ottimizzando la vicinanza di posizione (distanza di Manhattan).
        """
        #AttributeError: 'OrderItem' object has no attribute 'x'
        orders = set(self.orders_list)
        while len(orders) >= self.batch_size:
            batch = []
            # Seleziona un ordine iniziale casuale
            order = orders.pop()
            batch.append(order)

            # Seleziona gli ordini con la minima distanza di Manhattan
            for _ in range(self.batch_size-1):
                next_order = min(
                    orders,
                    key=lambda x: self.calculate_average_path_distance(order, x)
                )
                batch.append(next_order)
                orders.remove(next_order)

            self.batches.append(batch)

    def create_batches_by_weight(self):
        #AttributeError: 'Order' object has no attribute 'total_weight'
        """
        Crea batch di 4 ordini ottimizzando il peso totale del batch.
        """
        

        orders = set(self.orders_list)

        while len(orders) >= self.batch_size:
            batch = []
            # Seleziona un ordine iniziale casuale
            order = orders.pop()
            batch.append(order)

            # Aggiungi gli ordini che mantengono il peso del batch il più basso possibile
            for _ in range(self.batch_size-1):
                next_order = min(orders, key=lambda x: x.total_weight())
                batch.append(next_order)
                orders.remove(next_order)

            self.batches.append(batch)
    def create_batches_by_default(self):
        batches = []
        for i in range(0, len(self.orders_list), self.batch_size): 
            batch = self.orders_list[i:i + self.batch_size]
            batches.append(batch)
        self.batches = batches
    def calculate_average_path_distance(self, order1, order2):
        distance = 0
        count = 0
        for item_1 in order1.order_items:
            for item_2 in order2.order_items:
                distance += distance_compute_path((item_1.location[0].get_location_x(), item_1.location[0].get_location_y()),(item_2.location[0].get_location_x(), item_2.location[0].get_location_y()) )
                count += 1
        return distance / count if count > 0 else 0


#print(batch)


 
#the orders and the warheouse are previously created
o_orders = pickle.load(open('orders_list.pkl', 'rb'))
#print(o_orders)
o_warehouse : Warehouse = pickle.load(open('warehouse.pkl', 'rb'))
o_abc = pickle.load(open('abc_categories.pkl', 'rb'))
#print(o_abc)
#primer_batch = o_orders[1:5]

#batch = OrderBatch(1, primer_batch)
import mesa
import pickle
import random
from itertools import combinations

#o_orders = pickle.load(open('orders_list.pkl', 'rb'))
#parole chiave per batch weight, items, distance, default
#print(o_orders)


storage_policies = {'v': 'vertical', 'h': 'horizontal', 'hh': 'double_horizontal', 'o': 'oblique', 'oo': 'double_oblique', 'random': 'original'}
possible_io ={'c': 'centered', 'l': 'left','f': 'full'}
routing_policies = {'t': 'traversal', 'r': 'return', 'd': 'default', 'r2' : 'return_v2'}
batching_methods = {'d': 'distance', 'w':'weight', 'i': 'items', 'df': 'default' }
assignation_methods = {'p': 'productivity', 'pp': 'picker_preference', 'o': 'ordered', 'r2' : 'return_v2'}


# MODIFY THE FOLLOWING VARIABLES TO SETUP RUNNING CONFIGURATIONS
storage_policy = storage_policies['hh']
routing_policy = routing_policies['r2']
io_position = possible_io['f']
batching_mode = True #activates or deactivates the batching
batching_method = batching_methods['d']
batching_size = 6
order_assignation  = assignation_methods['r2']

#to change the io/positions
o_warehouse._set_io_positions(io_position) 
#to position the inventory
o_warehouse.reshuffle(storage_policy)
#this is to count the id of the plots
o_warehouse.cuenta = {0:0, 1:0, 2:0, 3:0}
#this sets true plots every path for picker and amr
o_warehouse.graph = False
if storage_policy == 'original': 
    o_orders = pickle.load(open('orders_list_original.pkl', 'rb'))
    
else:
    o_orders = pickle.load(open('orders_list.pkl', 'rb'))

o_warehousemodel = WarehouseModel(
    warehouse=o_warehouse, n_pickers=2, n_amr=2, orders=o_orders, 
    batching= batching_mode, batching_method = batching_method, 
    batch_size = batching_size, routing_policy= routing_policy, assignation_method = order_assignation)



# -*- coding: utf-8 -*-


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
