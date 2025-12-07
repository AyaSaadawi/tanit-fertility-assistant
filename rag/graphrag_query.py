"""
Simplified GraphRAG Query Engine
For demo purposes - queries the JSON knowledge base
"""

import json
import os
from typing import Dict, List

class GraphRAGEngine:
    def __init__(self, index_path="rag/graphrag_index"):
        """
        Load the knowledge base JSON
        """
        self.index_path = index_path
        kb_file = os.path.join(index_path, "knowledge_base.json")
        
        if not os.path.exists(kb_file):
            raise FileNotFoundError(
                f"Knowledge base not found at {kb_file}\n"
                "Please run: python rag/graphrag_builder.py first!"
            )
        
        with open(kb_file, 'r') as f:
            self.knowledge_base = json.load(f)
        
        print(f"✅ GraphRAG loaded: {len(self.knowledge_base)} entities")
    
    def query(self, query_text: str, top_k: int = 5, include_subgraph: bool = True) -> Dict:
        """
        Query the knowledge base using keyword matching
        Returns relevant entities and formatted context
        """
        query_lower = query_text.lower()
        
        # Keywords for entity matching
        keyword_map = {
            "amh": ["amh_levels"],
            "anti-müllerian": ["amh_levels"],
            "ovarian reserve": ["amh_levels", "fsh_levels"],
            "pcos": ["pcos", "amh_levels"],
            "polycystic": ["pcos"],
            "fsh": ["fsh_levels"],
            "follicle stimulating": ["fsh_levels"],
            "cycle": ["cycle_tracking"],
            "ovulation": ["cycle_tracking"],
            "fertile window": ["cycle_tracking"],
            "tracking": ["cycle_tracking"]
        }
        
        # Find relevant entities
        relevant_entities = set()
        for keyword, entities in keyword_map.items():
            if keyword in query_lower:
                relevant_entities.update(entities)
        
        # If no specific match, return general overview
        if not relevant_entities:
            relevant_entities = set(list(self.knowledge_base.keys())[:2])
        
        # Build response
        nodes = []
        relationships = []
        sources = set()
        
        for entity_key in relevant_entities:
            if entity_key in self.knowledge_base:
                entity_data = self.knowledge_base[entity_key]
                
                nodes.append({
                    "name": entity_key.replace("_", " ").title(),
                    "description": entity_data.get("description", ""),
                    "data": entity_data
                })
                
                # Extract sources
                if "sources" in entity_data:
                    sources.update(entity_data["sources"])
        
        # Format context for LLM
        formatted_context = self._format_context(nodes, list(sources))
        
        return {
            "nodes": nodes,
            "relationships": relationships,
            "sources": list(sources),
            "formatted_context": formatted_context
        }
    
    def _format_context(self, nodes: List[Dict], sources: List[str]) -> str:
        """
        Format knowledge base results for LLM consumption
        """
        context = "## Relevant Medical Knowledge from GraphRAG:\n\n"
        
        for node in nodes:
            context += f"### {node['name']}\n"
            context += f"{node['description']}\n\n"
            
            data = node['data']
            
            # Add specific details based on entity type
            if "normal_ranges" in data:
                context += "**Age-Specific Reference Ranges:**\n"
                for age, range_val in data["normal_ranges"].items():
                    context += f"- {age.replace('_', '-').replace('age ', 'Age ')}: {range_val}\n"
                context += "\n"
            
            if "interpretation" in data:
                context += "**Clinical Interpretation:**\n"
                for level, meaning in data["interpretation"].items():
                    context += f"- {level.title()}: {meaning}\n"
                context += "\n"
            
            if "clinical_notes" in data:
                context += "**Important Clinical Notes:**\n"
                for note in data["clinical_notes"]:
                    context += f"- {note}\n"
                context += "\n"
            
            if "fertility_impact" in data:
                context += "**Fertility Impact:**\n"
                for impact in data["fertility_impact"]:
                    context += f"- {impact}\n"
                context += "\n"
            
            if "diagnosis_criteria" in data:
                context += f"**Diagnosis:** {data['diagnosis_criteria']}\n\n"
            
            if "amh_relationship" in data:
                context += f"**AMH Relationship:** {data['amh_relationship']}\n\n"
        
        # Add sources
        if sources:
            context += "\n### Medical Sources:\n"
            for source in sources:
                context += f"- {source}\n"
        
        return context