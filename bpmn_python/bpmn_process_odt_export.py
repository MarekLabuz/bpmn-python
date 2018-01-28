# coding=utf-8
"""
Implementation of exporting process to ODT functionality
Process Modeling" by Środa K. and Łabuz M.
"""

import copy
import errno
import os
import sys

from odf import easyliststyle
from odf.opendocument import OpenDocumentText
from odf.text import P, List, ListItem

sys.path.append("/Users/marek/Documents/uni/bpmn-python")

import bpmn_python.bpmn_python_consts as consts
import bpmn_python.bpmn_diagram_exception as bpmn_exception
import bpmn_python.bpmn_import_utils as utils
import bpmn_process_csv_export as bpmn_csv_export
import bpmn_diagram_rep as diagram


class BpmnDiagramGraphOdtExport(object):
    """
    Class that provides implementation of exporting process to ODT functionality
    """

    def __init__(self):
        pass

    @staticmethod
    def export_process_to_odt(bpmn_diagram, directory, filename):
        """
        Root method of ODT export functionality.
        :param bpmn_diagram: an instance of BpmnDiagramGraph class,
        :param directory: a string object, which is a path of output directory,
        :param filename: a string object, which is a name of output file.
        """
        nodes = copy.deepcopy(bpmn_diagram.get_nodes())
        start_nodes = []
        export_elements = []

        for node in nodes:
            incoming_list = node[1].get(consts.Consts.incoming_flow)
            if len(incoming_list) == 0:
                start_nodes.append(node)
        if len(start_nodes) != 1:
            raise bpmn_exception.BpmnPythonError("Exporting to ODT format accepts only one start event")

        nodes_classification = utils.BpmnImportUtils.generate_nodes_clasification(bpmn_diagram)
        start_node = start_nodes.pop()
        bpmn_csv_export.BpmnDiagramGraphCsvExport\
            .export_node(bpmn_diagram, export_elements, start_node, nodes_classification)

        try:
            os.makedirs(directory)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

        item_list = BpmnDiagramGraphOdtExport.p(export_elements)
        item_list = BpmnDiagramGraphOdtExport.reassign_goto(item_list, export_elements)
        item_list = map(lambda item: item["Prefix"] + item["Label"], item_list)

        odt_file = directory + filename
        BpmnDiagramGraphOdtExport.write_export_node_to_file(odt_file, item_list)

    @staticmethod
    def reassign_goto(item_list, export_elements):
        """
        Reassigning goto activities adequately to the list numbering.
        :param item_list: TODO,
        :param export_elements: TODO.
        """
        print("\n".join(map(lambda x: x["Order"] + "\t" + x["Activity"], export_elements)))
        result = item_list[:]
        for index, item in enumerate(item_list):
            if item["Label"].startswith("goto"):
                order = item["Label"].replace("goto ", "")
                filtered_arr_order = list(filter(lambda elem: elem["Order"] == order, export_elements))
                print(filtered_arr_order, item)
                if len(filtered_arr_order) > 0:
                    activity = filtered_arr_order[0]["Activity"]
                    print(activity)
                    i = len(item_list) - 1
                    while i > 0:
                        if item_list[i]["Label"] == activity:
                            break
                        i -= 1

                    prefix = item_list[i]["Prefix"]
                    depth = len(prefix)

                    position = [1] * (depth + 1)

                    i -= 1
                    while i >= 0 and depth >= 0:
                        if len(item_list[i]["Prefix"]) == depth:
                            position[depth] += 1

                        if len(item_list[i]["Prefix"]) < depth:
                            depth -= 1

                        i -= 1

                    new_prefix = ".".join(map(lambda n: str(n), position)) + "."
                    print(item_list[i])
                    result[index]["Label"] = "goto " + new_prefix
        return result

    @staticmethod
    def prefix(n):
        """
        Reassigning goto activities adequately to the list numbering.
        :param n: TODO.
        """
        return "".join([">"] * n)

    @staticmethod
    def p(arr, last_order="0", depth=0, last_condition=""):
        """
        TODO.
        :param arr: TODO,
        :param last_order: TODO,
        :param depth: TODO,
        :param last_condition: TODO.
        """
        if len(arr) == 0:
            return []

        first, rest = arr[0], arr[1:]

        order_length = len(last_order)
        new_depth = depth
        result = []

        order = first["Order"]
        activity = first["Activity"]
        condition = first["Condition"]
        terminated = first["Terminated"]

        if terminated == "yes":
            activity = activity if activity != "" else "Terminate"

        if activity == "":
            return BpmnDiagramGraphOdtExport.p(rest, last_order, depth, last_condition)

        if len(order) < order_length:
            new_depth -= 2 if last_condition != "" else 1

        if len(order) == order_length and len(order) >= 3 and last_order[:-1] != order[:-1] and condition != "":
            result.append({"Prefix": BpmnDiagramGraphOdtExport.prefix(new_depth - 1), "Label": "If " + condition})

        new_condition = last_condition
        if len(order) > order_length:
            new_condition = condition
            if condition != "":
                result.append({"Prefix": BpmnDiagramGraphOdtExport.prefix(new_depth + 1), "Label": "If " + condition})
                new_depth += 2
            else:
                new_depth += 1

        result.append({"Prefix": BpmnDiagramGraphOdtExport.prefix(new_depth), "Label": activity})

        return result + BpmnDiagramGraphOdtExport.p(rest, order, new_depth, new_condition)

    @staticmethod
    def create_list(item_list, indent_delim, style_name):
        """
        TODO.
        :param item_list: TODO,
        :param indent_delim: TODO,
        :param style_name: TODO.
        """
        list_array = []
        last_level = 0

        for _ in range(0, 10):
            list_array.append(None)
        list_array[0] = List()

        for item in item_list:
            level = 0
            while level < len(item) and item[level] == indent_delim:
                level += 1
            item = item[level:]

            if level > last_level:
                for lev_count in range(last_level + 1, level + 1):
                    list_array[lev_count] = List()
            elif level < last_level:
                for lev_count in range(last_level, level, -1):
                    list_array[lev_count - 1].childNodes[-1].addElement(list_array[lev_count])

            list_array[level].setAttribute("stylename", style_name)
            list_item = ListItem()
            para = P(text=item)
            list_item.addElement(para)
            list_array[level].addElement(list_item)
            last_level = level

        for lev_count in range(last_level, 0, -1):
            list_array[lev_count - 1].childNodes[-1].addElement(list_array[lev_count])
        return list_array[0]

    @staticmethod
    def write_export_node_to_file(odt_file, item_list):
        """
        Exporting process to ODT file.
        :param odt_file: ODT file pathname,
        :param item_list: array of strings with document list items.
        """
        mixed_list_spec = '1.,1.,1.,1.,1.,1.'

        textdoc = OpenDocumentText()

        s = textdoc.styles

        list_style = easyliststyle.styleFromString("mix", mixed_list_spec, ",", "0.8cm", easyliststyle.SHOW_ONE_LEVEL)
        s.addElement(list_style)

        list_element = BpmnDiagramGraphOdtExport.create_list(item_list, ">", "mix")
        textdoc.text.addElement(list_element)

        textdoc.save(odt_file)


if __name__ == "__main__":
    bpmn_graph = diagram.BpmnDiagramGraph()
    bpmn_graph.load_diagram_from_xml_file(os.path.abspath("diagram.bpmn"))
    bpmn_graph.export_odt_file('./', "diagram.odt")
