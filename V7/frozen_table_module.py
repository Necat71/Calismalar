from PyQt6.QtWidgets import (
    QTableView,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
    QHeaderView,
    QAbstractItemView,
    QDialog,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, QDate
from PyQt6.QtGui import QColor, QBrush
import datetime
import sys


class FrozenTableModel(QAbstractTableModel):
    def __init__(self, main_model, frozen_column_count, parent=None):
        super().__init__(parent)
        self._main_model = main_model
        self._frozen_column_count = frozen_column_count
        # Ana model sinyallerini bağla
        # Ensure that dataChanged is properly connected to propagate changes
        self._main_model.dataChanged.connect(self._on_main_data_changed)
        # Handle row/column insertions/removals if main_table model can change structure
        self._main_model.rowsInserted.connect(self.rowsInserted)
        self._main_model.rowsRemoved.connect(self.rowsRemoved)
        self._main_model.columnsInserted.connect(self.columnsInserted)
        self._main_model.columnsRemoved.connect(self.columnsRemoved)
        self._main_model.headerDataChanged.connect(
            self.headerDataChanged
        )  # Propagate header changes

    def _on_main_data_changed(self, topLeft, bottomRight, roles):
        # Only emit dataChanged for the frozen columns
        if topLeft.column() < self._frozen_column_count:
            # Adjust bottomRight column if it exceeds frozen_column_count
            adjusted_bottom_right_col = min(
                bottomRight.column(), self._frozen_column_count - 1
            )
            # Create new QModelIndex for adjusted range
            adjusted_bottomRight = self.createIndex(
                bottomRight.row(), adjusted_bottom_right_col
            )
            self.dataChanged.emit(topLeft, adjusted_bottomRight, roles)

    def rowCount(self, parent=QModelIndex()):
        return self._main_model.rowCount(parent)

    def columnCount(self, parent=QModelIndex()):
        return min(self._frozen_column_count, self._main_model.columnCount(parent))

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.column() >= self._frozen_column_count:
            return None
        # Retrieve data from the main model
        return self._main_model.data(
            self._main_model.index(index.row(), index.column()), role
        )

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if (
            orientation == Qt.Orientation.Horizontal
            and section >= self._frozen_column_count
        ):
            return None
        return self._main_model.headerData(section, orientation, role)


class FrozenTableWidget(QWidget):
    def __init__(self, main_table, frozen_cols, parent=None):
        super().__init__(parent)
        self.main_table = main_table
        self.frozen_cols = frozen_cols

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Frozen view
        self.frozen_view = QTableView()
        # Set the model for the frozen view
        self.frozen_view.setModel(
            FrozenTableModel(self.main_table.model(), self.frozen_cols)
        )

        # Hide vertical scroll bar for the frozen view
        self.frozen_view.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        # Set horizontal header resize mode for frozen view to Fixed
        self.frozen_view.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Fixed
        )

        # Main table setup for scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.main_table)
        self.scroll_area.setWidgetResizable(True)

        # Set horizontal header resize mode for main table to Interactive
        self.main_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )

        
        self.layout.addWidget(self.frozen_view, 1)  # Stretch factor 1
        self.layout.addWidget(self.scroll_area, 3)  # Stretch factor 3

        # Set up synchronization
        self._setup_synchronization()

        # to adjust the widths of the frozen columns.
        self.main_table.horizontalHeader().sectionResized.connect(
            self.adjust_frozen_column_widths
        )

        # Also, initially adjust widths
        self.adjust_frozen_column_widths()

        # Hide vertical header for both views if desired (often for frozen tables)
        self.frozen_view.verticalHeader().hide()
        self.main_table.verticalHeader().hide()  # Usually hidden if frozen view's is hidden

    def _setup_synchronization(self):
        # Vertical scroll bar synchronization
        self.main_table.verticalScrollBar().valueChanged.connect(
            self.frozen_view.verticalScrollBar().setValue
        )
        self.frozen_view.verticalScrollBar().valueChanged.connect(
            self.main_table.verticalScrollBar().setValue
        )  # Ensure two-way sync if user scrolls frozen view


    def adjust_frozen_column_widths(self):
        """
        Dondurulmuş sütunların genişliklerini ana tablodaki karşılık gelen sütun genişlikleriyle senkronize eder.
        """
        header = self.main_table.horizontalHeader()
        frozen_header = self.frozen_view.horizontalHeader()
        for i in range(min(self.frozen_cols, header.count())):
            width = header.sectionSize(i)
            frozen_header.resizeSection(i, width)
