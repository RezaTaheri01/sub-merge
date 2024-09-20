import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QMessageBox, QHBoxLayout, QFrame, QDesktopWidget
)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt
import qdarkstyle


class FileMergerApp(QWidget):
    def __init__(self):
        super().__init__()

        self.file1_path = None
        self.file2_path = None

        self.initUI()

    def initUI(self):
        # Lunch at center of the screen
        def center_window():
            qtRectangle = self.frameGeometry()
            centerPoint = QDesktopWidget().availableGeometry().center()
            qtRectangle.moveCenter(centerPoint)
            self.move(qtRectangle.topLeft())

        # Main layout
        main_layout = QVBoxLayout()

        # File selection layout
        file_layout1 = QHBoxLayout()
        file_layout2 = QHBoxLayout()

        # Labels to show selected files
        self.label1 = QLabel('First Sub:')
        self.label1.setFont(QFont("Arial", 10, QFont.Bold))
        self.label1.setFrameShape(QFrame.Panel)
        self.label1.setFrameShadow(QFrame.Sunken)

        self.label2 = QLabel('Second Sub:')
        self.label2.setFont(QFont("Arial", 10, QFont.Bold))
        self.label2.setFrameShape(QFrame.Panel)
        self.label2.setFrameShadow(QFrame.Sunken)

        # Buttons to select files
        self.btn_file1 = QPushButton('Browse...')
        self.btn_file1.clicked.connect(self.select_file1)

        self.btn_file2 = QPushButton('Browse...')
        self.btn_file2.clicked.connect(self.select_file2)

        # Add widgets to file layouts
        file_layout1.addWidget(self.label1)
        file_layout1.addWidget(self.btn_file1)

        file_layout2.addWidget(self.label2)
        file_layout2.addWidget(self.btn_file2)

        # Merge Button
        self.btn_merge = QPushButton('Merge Files')
        self.btn_merge.setFont(QFont("Arial", 12, QFont.Bold))
        self.btn_merge.clicked.connect(self.merge_files)
        self.btn_merge.setStyleSheet(
            "background-color: #4CAF50; color: white; padding: 10px 20px;")

        # Add all widgets to main layout
        main_layout.addLayout(file_layout1)
        main_layout.addLayout(file_layout2)
        main_layout.addWidget(self.btn_merge, alignment=Qt.AlignCenter)

        self.setLayout(main_layout)
        
        # Set main window properties
        self.setWindowIcon(QIcon('./images/SubMerge.ico'))
        self.setWindowTitle('Subtitle File Merger')
        self.setGeometry(500, 300, 500, 150)
        center_window()
        
        # Disable the maximize button by modifying the window flags
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)
        
        # Optional: Disable resizing the window
        self.setFixedSize(self.size())

    def select_file1(self):
        file1, _ = QFileDialog.getOpenFileName(self, 'Select first subtitle')
        if file1:
            self.file1_path = file1
            short_name = file1.split("/")[-1]
            self.label1.setText(f'Selected: {short_name[:10]}...')
            self.label1.setToolTip(file1)

    def select_file2(self):
        file2, _ = QFileDialog.getOpenFileName(self, 'Select second subtitle')
        if file2:
            self.file2_path = file2
            short_name = file2.split("/")[-1]
            self.label2.setText(f'Selected: {short_name[:10]}...')
            self.label2.setToolTip(file2)

    def merge_files(self):
        if not self.file1_path or not self.file2_path:
            QMessageBox.warning(
                self, 'Error', 'Please select both files to merge.')
            return

        # Reading files
        try:
            merged_data = self.main(self.file1_path, self.file2_path)

            # Saving the merged file
            save_path, _ = QFileDialog.getSaveFileName(
                self, 'Save merged file')
            if save_path:
                with open(save_path, 'w') as f:
                    f.write(merged_data)
                QMessageBox.information(
                    self, 'Success', 'Files merged successfully!')

        except Exception as e:
            QMessageBox.critical(self, 'Error', f'An error occurred: {e}')

    # Split each line of subtitle
    def split_regions(self, file_path, sec: bool):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()

        # Split content by double newline to separate regions
        regions = content.split('\n\n')

        # Remove the first line (index number) from each region
        pre = None
        if sec:
            pre = '{\\an8}'
        cleaned_regions = []
        for region in regions:
            lines = region.splitlines()
            if pre and lines[2][:6] != pre:
                lines[2] = pre + lines[2]
            cleaned_region = "\n".join(lines[1:])  # Exclude the first line
            cleaned_regions.append(cleaned_region)
        return cleaned_regions

    def time_to_seconds(self, time_str):
        h, m, s = map(int, time_str.split(':'))
        return h * 3600 + m * 60 + s

    # Get start time for each sub line
    def getTimes(self, sub: list, prefix):
        tmp = []
        for i in range(len(sub)):
            line = sub[i].split('\n')[0]
            if line[13:16] == '-->':
                tmp.append(
                    f'{prefix}{self.time_to_seconds(line.split(",")[0])}')
        return tmp

    # Sort time list of two subtitles
    def sortTimes(self, t1: list, t2: list):
        p1 = p2 = 0
        tmp = []

        while p1 < len(t1) and p2 < len(t2):
            if int(t1[p1][1:]) <= int(t2[p2][1:]):
                tmp.append(t1[p1])
                p1 += 1
            else:
                tmp.append(t2[p2])
                p2 += 1

        return tmp

    # Base on sortTimes output create new subtitle (2 pointer)
    def mergeSubs(self, timeline, p_sub, s_sub):
        p_pointer = s_pointer = 0
        counter = 1
        string = ''
        for t in timeline:
            if t[0] == 'p':
                string += str(counter) + '\n' + p_sub[p_pointer] + '\n\n'
                p_pointer += 1
                counter += 1
            else:
                string += str(counter) + '\n' + s_sub[s_pointer] + '\n\n'
                s_pointer += 1
                counter += 1
        return string

    def main(self, primary_path, secondary_path):
        # primary sub is always on top {}
        primary_sub = self.split_regions(primary_path, False)
        secondary_sub = self.split_regions(secondary_path, True)

        times_p = self.getTimes(primary_sub, 'p')
        times_s = self.getTimes(secondary_sub, 's')

        # sort times
        newTimeLine = self.sortTimes(times_p, times_s)
        new_sub = self.mergeSubs(newTimeLine, primary_sub, secondary_sub)
        return new_sub


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    ex = FileMergerApp()
    ex.show()
    sys.exit(app.exec_())
