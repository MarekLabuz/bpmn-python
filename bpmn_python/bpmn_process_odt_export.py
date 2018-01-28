# coding=utf-8
"""
Implementation of exporting process to ODT functionality
Process Modeling" by Środa K. and Łabuz M.
"""

import copy
import errno
import os

from odf import easyliststyle
from odf.opendocument import OpenDocumentText
from odf.text import P, List, ListItem
import bpmn_python.bpmn_python_consts as consts
import bpmn_python.bpmn_diagram_exception as bpmn_exception
import bpmn_python.bpmn_import_utils as utils
import bpmn_python.bpmn_process_csv_export as bpmn_csv_export


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

        item_list = BpmnDiagramGraphOdtExport.transform_into_list_items(export_elements)
        item_list = BpmnDiagramGraphOdtExport.reassign_goto(item_list, export_elements)
        item_list = map(lambda item: item["Prefix"] + item["Label"], item_list)

        odt_file = directory + filename
        BpmnDiagramGraphOdtExport.write_export_node_to_file(odt_file, item_list)

    @staticmethod
    def reassign_goto(item_list, export_elements):
        """
        Reassigning goto activities adequately to the list numbering.
        :param item_list: array of list items,
        :param export_elements: array of dictionaries with activities parameters.
        """
        result = item_list[:]
        for index, item in enumerate(item_list):
            if item["Label"].startswith("goto"):
                order = item["Label"].replace("goto ", "")
                filtered_arr_order = list(filter(lambda elem: elem["Order"] == order, export_elements))
                if len(filtered_arr_order) > 0:
                    activity = filtered_arr_order[0]["Activity"]
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
                    result[index]["Label"] = "goto " + new_prefix
        return result

    @staticmethod
    def prefix(n):
        """
        Reassigning goto activities adequately to the list numbering.
        :param n: nesting depth of list item.
        """
        return "".join([">"] * n)

    @staticmethod
    def transform_into_list_items(export_elements, last_order="0", depth=0, last_condition=""):
        """
        TODO.
        :param export_elements: array of dictionaries with activities parameters,
        :param last_order: order of previous list item,
        :param depth: nesting depth of list item,
        :param last_condition: condition of previous list item.
        """
        if len(export_elements) == 0:
            return []

        first, rest = export_elements[0], export_elements[1:]

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
            return BpmnDiagramGraphOdtExport.transform_into_list_items(rest, last_order, depth, last_condition)

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

        return result + BpmnDiagramGraphOdtExport.transform_into_list_items(rest, order, new_depth, new_condition)

    @staticmethod
    def create_list(item_list, indent_delim, style_name):
        """
        TODO.
        :param item_list: array of list items,
        :param indent_delim: char identifying the nesting depth of list items,
        :param style_name: easyliststyle identifier.
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
