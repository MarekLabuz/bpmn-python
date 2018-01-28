# coding=utf-8
"""
Unit tests for exporting process to ODT functionality.
"""

import os
import unittest

import bpmn_python.bpmn_diagram_rep as diagram


class CsvExportTests(unittest.TestCase):
    """
    This class contains test for manual diagram generation functionality.
    """
    output_directory = "./output/test-odt-export/"
    example_directory = "../examples/odt_export/"

    def test_odt_export_bank_account_example(self):
        bpmn_graph = diagram.BpmnDiagramGraph()
        bpmn_graph.load_diagram_from_xml_file(os.path.abspath(self.example_directory + "bank-account-process.bpmn"))
        bpmn_graph.export_odt_file(self.output_directory, "bank-account-process.odt")

    def test_odt_export_nested_gates_example(self):
        bpmn_graph = diagram.BpmnDiagramGraph()
        bpmn_graph.load_diagram_from_xml_file(os.path.abspath(self.example_directory + "nested-gates.bpmn"))
        bpmn_graph.export_odt_file(self.output_directory, "nested-gates.odt")

if __name__ == '__main__':
    unittest.main()
