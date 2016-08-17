import xml.etree.ElementTree as etree

class Parser:
   def __init__(self, filename):
      self.tree = etree.parse('filename')
      self.root = self.tree.getroot()


class MobData(Parser):
   def __init__(self, filename):
      Parser.__init__(filename)
      self._parse()

   def _parse():
      self.data = []
      #TODO add error checking!
      for mob in self.root:
         entry = []
         entry['name'] = mob['name']
         entry['color'] = mob['color']
         entry['character'] = mob['character']
         entry['ai_type'] = mob['ai_type']
         entry['attributes'] = []
         for attribute in mob['attributes']:
            attribute['attributes'].append(attribute['entry'])
         entry['danger_level'] = mob['danger_level']
         entry['danger_table'] = []
         for table_entry in mob['danger_table']:
            entry['danger_table'].append([table_entry.attrib['odds'], table_entry['level']])
         entry['hp'] = mob['hp']
         entry['defense'] = mob['defense']
         entry['power'] = mob['power']
         entry['xp'] = mob['xp']
         entry['description'] = mob['description']
         self.data.append(entry)


