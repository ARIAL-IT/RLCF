#!/usr/bin/env python3
"""
Script per convertire qa_dataset_004.xlsx in formato YAML compatibile con RLCF.

Questo script prende il dataset Excel e lo converte nel formato YAML richiesto
dal framework RLCF, separando automaticamente i dati di input da quelli di ground truth.
"""

import pandas as pd
import yaml
import sys
from pathlib import Path

def convert_qa_dataset_to_yaml(xlsx_path: str, output_path: str, max_records: int = None):
    """
    Converte il dataset QA da Excel a formato YAML per RLCF.
    
    Args:
        xlsx_path: Percorso del file Excel di input
        output_path: Percorso del file YAML di output
        max_records: Numero massimo di record da convertire (None = tutti)
    """
    
    print(f"Leggendo dataset da {xlsx_path}...")
    df = pd.read_excel(xlsx_path)
    
    if max_records:
        df = df.head(max_records)
        print(f"Limitando a {max_records} record...")
    
    print(f"Dataset caricato: {len(df)} record")
    print(f"Colonne disponibili: {list(df.columns)}")
    
    tasks = []
    
    for _, row in df.iterrows():
        # Preparazione input_data (quello che vedrà l'AI e gli evaluatori)
        input_data = {
            "question": str(row.get('question', '')),
            "context_full": str(row.get('context_full', '')),
            "relevant_articles": str(row.get('relevant_articles', '')),
            "category": str(row.get('category', ''))
        }
        
        # Ground truth (per calcolare correctness)
        input_data["answer_text"] = str(row.get('answer_text', ''))
        
        # Metadati aggiuntivi se disponibili
        if 'tags' in row and pd.notna(row['tags']):
            input_data["tags"] = str(row['tags'])
        
        if 'rule_id' in row and pd.notna(row['rule_id']):
            input_data["rule_id"] = str(row['rule_id'])
            
        task = {
            "task_type": "STATUTORY_RULE_QA",
            "input_data": input_data
        }
        
        tasks.append(task)
    
    # Struttura YAML finale
    yaml_data = {
        "tasks": tasks,
        "metadata": {
            "source": "qa_dataset_004.xlsx",
            "total_tasks": len(tasks),
            "description": "Legal Q&A tasks for statutory rules and regulations",
            "task_type": "STATUTORY_RULE_QA"
        }
    }
    
    print(f"Scrivendo {len(tasks)} tasks in {output_path}...")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True, indent=2)
    
    print("✅ Conversione completata!")
    print(f"📁 File generato: {output_path}")
    print(f"📊 Task creati: {len(tasks)}")
    
    # Stampa esempio del primo task
    if tasks:
        print("\n📝 Esempio del primo task:")
        print(yaml.dump({"example_task": tasks[0]}, default_flow_style=False, allow_unicode=True, indent=2))

def main():
    # Configurazione
    base_dir = Path(__file__).parent
    input_file = base_dir / "datasets" / "qa_dataset_004.xlsx"
    output_file = base_dir / "datasets" / "qa_dataset_004_rlcf.yaml"
    
    # Opzione per limitare i record (utile per test)
    max_records = None
    if len(sys.argv) > 1:
        try:
            max_records = int(sys.argv[1])
            output_file = base_dir / "datasets" / f"qa_dataset_004_rlcf_sample_{max_records}.yaml"
        except ValueError:
            print("❌ Errore: Il parametro deve essere un numero (max_records)")
            sys.exit(1)
    
    if not input_file.exists():
        print(f"❌ File non trovato: {input_file}")
        sys.exit(1)
    
    convert_qa_dataset_to_yaml(str(input_file), str(output_file), max_records)

if __name__ == "__main__":
    main()