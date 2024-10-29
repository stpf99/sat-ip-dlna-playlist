import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QComboBox, QPushButton, QLabel, 
                           QTabWidget, QGroupBox, QCheckBox, QMessageBox)
from PyQt5.QtCore import Qt
import os
import subprocess

class SatelliteConfigGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TRIAX TSS400 DLNA channels xml wizard ")
        self.setMinimumWidth(800)
        self.setMinimumHeight(400)
        
        # Available satellite positions (can be expanded)
        self.satellite_positions = {
            "13.0E": "13E",
            "19.2E": "19.2E",
            "23.5E": "23.5E",
            "28.2E": "28.2E",
            "31.5E": "31.5E",
            "39.0E": "39E",
            "45.0E": "45E"
        }
        
        # Available languages (add more)
        self.languages = ["eng", "pol", "ger", "fre", "ita", "spa", "cze", "hun"]
        
        self.init_ui()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        tab_widget = QTabWidget()
        
        # Create tabs for simple and DiSEqC modes
        simple_tab = self.create_simple_tab()
        diseqc_tab = self.create_diseqc_tab()
        
        tab_widget.addTab(simple_tab, "Simple Mode (Single LNB)")
        tab_widget.addTab(diseqc_tab, "DiSEqC Mode (4 LNB)")
        
        layout.addWidget(tab_widget)
        
    def create_simple_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Satellite position selection
        pos_group = QGroupBox("Satellite Position")
        pos_layout = QHBoxLayout()
        self.simple_pos_combo = QComboBox()
        self.simple_pos_combo.addItems(self.satellite_positions.keys())
        pos_layout.addWidget(QLabel("Position:"))
        pos_layout.addWidget(self.simple_pos_combo)
        pos_group.setLayout(pos_layout)
        
        # Language selection
        lang_group = QGroupBox("Languages")
        lang_layout = QVBoxLayout()
        self.simple_lang_checks = []
        for lang in self.languages:
            check = QCheckBox(lang.upper())
            self.simple_lang_checks.append(check)
            lang_layout.addWidget(check)
        lang_group.setLayout(lang_layout)
        
        # Generate button
        generate_btn = QPushButton("Generate Channel List")
        generate_btn.clicked.connect(self.generate_simple_config)
        
        layout.addWidget(pos_group)
        layout.addWidget(lang_group)
        layout.addWidget(generate_btn)
        layout.addStretch()
        
        return widget
        
    def create_diseqc_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.diseqc_configs = []
        
        # Create 4 DiSEqC position configurations
        for i in range(4):
            group = QGroupBox(f"LNB {i+1}")
            group_layout = QHBoxLayout()
            
            pos_combo = QComboBox()
            pos_combo.addItems(self.satellite_positions.keys())
            
            group_layout.addWidget(QLabel("Position:"))
            group_layout.addWidget(pos_combo)
            
            group.setLayout(group_layout)
            layout.addWidget(group)
            
            self.diseqc_configs.append(pos_combo)
        
        # Language selection
        lang_group = QGroupBox("Languages")
        lang_layout = QVBoxLayout()
        self.diseqc_lang_checks = []
        for lang in self.languages:
            check = QCheckBox(lang.upper())
            self.diseqc_lang_checks.append(check)
            lang_layout.addWidget(check)
        lang_group.setLayout(lang_layout)
        
        # Generate button
        generate_btn = QPushButton("Generate Multi-Position Channel List")
        generate_btn.clicked.connect(self.generate_diseqc_config)
        
        layout.addWidget(lang_group)
        layout.addWidget(generate_btn)
        layout.addStretch()
        
        return widget
    
    def get_selected_languages(self, checks):
        return [lang.lower() for check, lang in zip(checks, self.languages) if check.isChecked()]
    
    def generate_simple_config(self):
        position = self.satellite_positions[self.simple_pos_combo.currentText()]
        languages = self.get_selected_languages(self.simple_lang_checks)
        
        if not languages:
            QMessageBox.warning(self, "Warning", "Please select at least one language.")
            return
            
        try:
            # Run king2xml.py with selected parameters
            cmd = ["python", "king2xml.py", position, "1"]
            cmd.extend(languages)
            
            subprocess.run(cmd, check=True)
            QMessageBox.information(self, "Success", "Channel list generated successfully!")
            
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Error", f"Failed to generate channel list: {str(e)}")
    
    def generate_diseqc_config(self):
        languages = self.get_selected_languages(self.diseqc_lang_checks)
        
        if not languages:
            QMessageBox.warning(self, "Warning", "Please select at least one language.")
            return
        
        try:
            # Create output directory
            os.makedirs("MULTIPOS", exist_ok=True)
            
            # Generate channel lists for each position
            for i, combo in enumerate(self.diseqc_configs, 1):
                position = self.satellite_positions[combo.currentText()]
                
                cmd = ["python", "king2xml.py", position, str(i)]
                cmd.extend(languages)
                
                subprocess.run(cmd, check=True)
                
                # Move the generated file to MULTIPOS directory
                src_pattern = f"TV-{position}-FTA-langs-{'-'.join(languages)}.xml"
                if os.path.exists(f"ONEPOSMULTILANG/{src_pattern}"):
                    os.rename(
                        f"ONEPOSMULTILANG/{src_pattern}",
                        f"MULTIPOS/pos{i}_{src_pattern}"
                    )
            
            self.merge_multiposition_files(languages)
            QMessageBox.information(self, "Success", "Multi-position channel list generated successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate multi-position channel list: {str(e)}")
    
    def merge_multiposition_files(self, languages):
        """Merges individual position files into a single multi-position file"""
        output_filename = f"MULTIPOS/TV-MULTIPOS-FTA-langs-{'-'.join(languages)}.xml"
        
        with open(output_filename, "w", encoding="utf-8") as outfile:
            outfile.write('<?xml version="1.0" encoding="UTF-8"?>\n<channelTable msys="DVB-S">\n')
            
            # Merge content from each position file
            for i in range(1, 5):
                for pos_combo in self.diseqc_configs:
                    position = self.satellite_positions[pos_combo.currentText()]
                    src_filename = f"MULTIPOS/pos{i}_TV-{position}-FTA-langs-{'-'.join(languages)}.xml"
                    
                    if os.path.exists(src_filename):
                        with open(src_filename, "r", encoding="utf-8") as infile:
                            content = infile.read()
                            # Extract channel entries (skip header and footer)
                            channels = content.split('\n')[1:-1]
                            outfile.write('\n'.join(channels) + '\n')
            
            outfile.write('</channelTable>')

def main():
    app = QApplication(sys.argv)
    window = SatelliteConfigGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
