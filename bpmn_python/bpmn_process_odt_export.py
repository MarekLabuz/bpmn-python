# coding=utf-8
"""
Implementation of exporting process to ODT functionality
Process Modeling" by Środa K. and Łabuz M.
"""

import copy
import errno
import os
import sys
import re

sys.path.append("/Users/marek/Documents/uni/bpmn-python")

import bpmn_python.bpmn_python_consts as consts
import bpmn_python.bpmn_diagram_exception as bpmn_exception
import bpmn_python.bpmn_import_utils as utils
import bpmn_python.bpmn_process_csv_export as bpmn_csv_export
import bpmn_diagram_rep as diagram

from odf import easyliststyle
from odf.opendocument import OpenDocumentText
from odf.text import P, List, ListItem


class BpmnDiagramGraphOdtExport(object):
    """
    Class that provides implementation of exporting process to ODT functionality
    """
    gateways_list = ["exclusiveGateway", "inclusiveGateway", "parallelGateway"]
    tasks_list = ["task", "subProcess"]

    classification_element = "Element"
    classification_start_event = "Start Event"
    classification_end_event = "End Event"
    classification_join = "Join"
    classification_split = "Split"

    '''
    Supported start event types: normal, timer, message.
    Supported end event types: normal, message.
    '''
    events_list = ["startEvent", "endEvent"]
    lanes_list = ["process", "laneSet", "lane"]

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

        print(export_elements)
        item_list = []

        for export_element in export_elements:
            l = len(re.sub(r"([a-z])+", "", export_element["Order"])) - 1
            prefix = ''.join([">"] * l)
            item_list.append(prefix + export_element["Activity"])

        odt_file = directory + filename
        BpmnDiagramGraphOdtExport.write_export_node_to_file(odt_file, item_list)

    @staticmethod
    def create_list(item_list, indent_delim, style_name):
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
        Exporting process to ODT file
        :param odt_file: TODO,
        :param item_list: TODO
        """
        mixed_list_spec = u'1.!\u273f!a)'

        textdoc = OpenDocumentText()

        s = textdoc.styles

        list_style = easyliststyle.styleFromString("mix", mixed_list_spec, "!", "0.8cm", easyliststyle.SHOW_ONE_LEVEL)
        s.addElement(list_style)

        list_element = BpmnDiagramGraphOdtExport.create_list(item_list, ">", "mix")
        textdoc.text.addElement(list_element)

        textdoc.save(odt_file)


if __name__ == "__main__":
    bpmn_graph = diagram.BpmnDiagramGraph()
    bpmn_graph.load_diagram_from_xml_file(os.path.abspath("pizza-order.bpmn"))
    bpmn_graph.export_odt_file('./', "pizza.odt")
