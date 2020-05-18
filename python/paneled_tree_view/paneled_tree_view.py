# -*- coding: utf-8 -*-
import os
import random
from collections import OrderedDict
import qtawesome
from mayaqt import *

# アイコン定義
dir_icon = qtawesome.icon('fa5s.{}'.format('folder'), color='lightgray')
checked_icon = qtawesome.icon('fa5s.{}'.format('check-square'), color='lightgray')
unchecked_icon = qtawesome.icon('fa5s.{}'.format('square'), color='lightgray')
down_icon = qtawesome.icon('fa5s.{}'.format('angle-down'), color='lightgray')
down_icon = qtawesome.icon('fa5s.{}'.format('caret-down'), color='lightgray')
right_icon = qtawesome.icon('fa5s.{}'.format('angle-right'), color='lightgray')
right_icon = qtawesome.icon('fa5s.{}'.format('caret-right'), color='lightgray')

# 色定義
transparency_color = QtGui.QColor(*[0]*4)
shadow_color = QtGui.QColor(0,0,0, 50)
panel_color = QtGui.QColor(*[86]*3)
text_color = QtGui.QColor(*[210]*3)
sub_text_color = QtGui.QColor(*[160]*3)
err_text_color = QtGui.QColor(255, 30, 30)
deactive_text_color = QtGui.QColor(*[30]*3)
default_tag_color = QtGui.QColor(*[73]*3)
selected_panel_color = QtGui.QColor(82, 133, 166)
selected_text_color = QtGui.QColor(*[255]*3)

class AbstractPanelItemData(object):
    def __init__(self, value=('temp', 'temp1'), attribute1=0, attribute2=1):
        self.value = value
        self.attribute1 = attribute1
        self.attribute2 = attribute2
        self.color = random.randint(60, 255), random.randint(60, 255), random.randint(60, 255)
        self.headers = 'value', 'attribute1', 'attribute2', 'color'

class PanelItem(object):
    
    def __init__(self, item_data=AbstractPanelItemData()):
        self.item_data = item_data
        self.parent_item = None

        if hasattr(self.item_data, 'headers'):
            self.headers = self.item_data.headers

        else:
            self.headers = [attr for attr in dir(self.item_data) if not attr.startswith('__')]

        self.child_items = []

    def add_child(self, item):
        item.parent_item = self
        self.child_items.append(item)

    def child(self, row):
        return self.child_items[row]

    def child_count(self):
        return len(self.child_items)

    def column_count(self):
        return len(self.headers)

    def data(self, column=0):
        if not column < len(self.headers):
            return None

        attr = self.headers[column]
        return getattr(self.item_data, attr)

    def parent(self):
        return self.parent_item

    def row(self):
        if self.parent_item:
            return self.parent_item.child_items.index(self)

        return 0

    def color(self):
        '''
        カラーを取得
        '''
        # 格納されたデータクラスがcolorを持っていれば返す
        if hasattr(self.item_data, 'color'):
            return self.item_data.color

class PanelItemModel(QtCore.QAbstractItemModel):

    def __init__(self, parent=None, item_class=PanelItem, headers=[]):
        super(PanelItemModel, self).__init__(parent)
        self.root_item = item_class()

    def columnCount(self, parent=None):
        if parent and parent.isValid():
            return parent.internalPointer().column_count()

        else:
            return self.root_item.column_count()

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None

        item = index.internalPointer()
        column = index.column()

        if role == QtCore.Qt.DisplayRole:
            return item.data(column)

        if role == QtCore.Qt.BackgroundRole:
            color = item.color()

            if color:
                return QtGui.QColor(*color)

            else:
                return default_tag_color

        return None

    def headerData(self, column, orientation=QtCore.Qt.Horizontal, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            return ''
            return self.root_item.headers[column]

        # elif role == QtCore.Qt.DecorationRole:
        #     return checked_icon

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            item = self.root_item

        else:
            item = parent.internalPointer()

        child_item = item.child(row)

        if child_item:
            return self.createIndex(row, column, child_item)

        else:
            return QtCore.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        item = index.internalPointer()

        if not item:
            return QtCore.QModelIndex()

        parent_item = item.parent()

        if parent_item == self.root_item:
            return QtCore.QModelIndex()

        return self.createIndex(parent_item.row(), 0, parent_item)
        
    def rowCount(self, parent=QtCore.QModelIndex()):
        if not parent.isValid():
            parent_item = self.root_item

        else:
            parent_item = parent.internalPointer()

        return parent_item.child_count()

class PanelItemDelegate(QtWidgets.QStyledItemDelegate):
    
    def __init__(self, parent=None):
        super(PanelItemDelegate, self).__init__(parent)
        self.height = 24
        self.panel_space_width = 0
        self.panel_space_height = 1
        self.panel_shadow_radio = 0.3
        self.text_space_width = 0
        self.text_space_height = 0
        self.text_align = QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter
        self.indent = 0
        self.panel_color = panel_color
        self.text_color = text_color
        self.odd_darker_factor = 5
        self.depth_darker_factor = 5

    def _get_depth(self, painter, option, index):
        parent = index.parent()
        depth = 0
        root_index = option.widget.rootIndex()

        while True:
            if not parent.isValid() or parent == root_index:
                break

            parent = parent.parent()
            depth += 1

        return depth

    def _get_panel_rect(self, painter, option, index, in_depth):
        '''
        アイテム描画矩形を取得
        元のものより一回り小さいものを返す
        '''
        indent = self.indent * in_depth

        rect = QtCore.QRect(
            option.rect.left() + self.panel_space_width + indent,
            option.rect.top() + self.panel_space_height,
            option.rect.width() - self.panel_space_width,
            option.rect.height() - self.panel_space_height
        )

        return rect

    def _draw_panel(self, painter, option, index, in_rect, in_selected, in_expanded, in_depth):
        '''
        背景描画
        '''
        if not index.isValid():
            return in_rect
        
        row = index.row()
        parent = index.parent()

        rect = QtCore.QRect(
            in_rect.left(),
            in_rect.top(),
            in_rect.width(),
            in_rect.height()
        )

        if in_selected:
            color = selected_panel_color

        else:
            color = self.panel_color

        if row % 2:
            color = color.darker(100 + self.odd_darker_factor)

        color = color.darker(100 + in_depth * self.depth_darker_factor)

        # 通常背景描画
        brush = QtGui.QBrush(color)
        pen = QtGui.QPen(transparency_color)
        painter.setBrush(brush)
        painter.setPen(pen)
        painter.drawRect(rect)

        return rect

    def _draw_panel_shadow(self, painter, option, index, in_rect, in_selected, in_expanded, in_depth):
        '''
        背景影描画
        '''
        if not index.isValid():
            return in_rect

        row = index.row()
        parent = index.parent()

        if not parent.isValid() or row != 0:
            return

        height = in_rect.height() * self.panel_shadow_radio
        
        rect = QtCore.QRect(
            in_rect.left(),
            in_rect.top(),
            in_rect.width(),
            height
        )

        grad = QtGui.QLinearGradient(0, in_rect.top(), 0, in_rect.top() + height)
        grad.setColorAt(0, shadow_color)
        grad.setColorAt(1, transparency_color)
        brush = QtGui.QBrush(grad)
        painter.setBrush(brush)
        painter.drawRect(rect)
        return rect

    def _get_text(self, option, index):
        value = index.data(QtCore.Qt.DisplayRole)
        
        # 入力がリストの場合文字列に変換
        if hasattr(value, '__iter__'):
            value = [unicode(value_) for value_ in value]

        else:
            value = [unicode(value)]

        value = ' : '.join(value)
        return value

    def _draw_text(self, painter, option, index, in_rect, in_selected, in_expanded, in_depth):
        row = index.row()
        text = self._get_text(option, index)
        color = self.text_color

        if row % 2:
            color = color.darker(100 + self.odd_darker_factor)

        color = color.darker(100 + in_depth * self.depth_darker_factor)

        rect = QtCore.QRect(
            in_rect.left() + self.text_space_width,
            in_rect.top(),
            in_rect.width(),
            in_rect.height()
        )

        pen = QtGui.QPen(color)
        painter.setPen(pen)
        painter.drawText(rect, self.text_align, text)
        return rect

    def paint(self, painter, option, index):
        has_children = option.state & QtWidgets.QStyle.State_Children
        expanded = option.state & QtWidgets.QStyle.State_Open
        selected = option.state & QtWidgets.QStyle.State_Selected
        parent = index.parent()
        depth = self._get_depth(painter, option, index)
        rect = self._get_panel_rect(painter, option, index, depth)

        # 背景描画
        panel_rect = self._draw_panel(painter, option, index, rect, selected, expanded, depth)
        shadow_rect = self._draw_panel_shadow(painter, option, index, panel_rect, selected, expanded, depth)

        # テキスト描画
        text_rect = self._draw_text(painter, option, index, rect, selected, expanded, depth)
        return rect, selected, expanded, depth, has_children

    def sizeHint(self, option, index):
        font = QtGui.QFont('Segoe UI', 11) # painterから取得できるものと同じ
        font_metrics = QtGui.QFontMetrics(font)
        text = self._get_text(option, index)
        width = font_metrics.width(text)
        rect = option.rect
        text = self._get_text(option, index)
        return QtCore.QSize(width, self.height)

class ValueColumnDelegate(PanelItemDelegate):

    def __init__(self, parent=None):
        super(ValueColumnDelegate, self).__init__(parent)
        # self.height = 80
        self.tag_width = 8
        self.tag_space_width = 2
        self.indent = 10
        self.panel_space_width = self.tag_width + self.tag_space_width
        self.text_space_width = self.height * 0.6
        self.text_align = QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft
        self.inherit_color = True

    def _get_color(self, index):
        color = color = index.data(QtCore.Qt.BackgroundRole)
        parent = index.parent()

        # parent_itemがない場合スキップすることでルートアイテムの色は判定しないようにする
        if self.inherit_color and parent.isValid():
            while True:
                if not parent.isValid():
                    break
                
                color = parent.data(QtCore.Qt.BackgroundRole)
                parent = parent.parent()

        if not color:
            color = default_tag_color

        return color

    def _draw_tag(self, painter, option, index, in_rect, in_selected, in_expanded, in_depth):
        rect = QtCore.QRect(
            self.indent * in_depth + self.tag_space_width,
            in_rect.top(),
            self.tag_width,
            in_rect.height()
        )

        color = self._get_color(index)
        color = color.darker(100 + in_depth * self.depth_darker_factor)
        brush = QtGui.QBrush(color)
        pen = QtGui.QPen(transparency_color)
        painter.setBrush(brush)
        painter.setPen(pen)
        painter.drawRect(rect)
        return rect

    def _draw_expand_icon(self, painter, option, index, in_rect, in_selected, in_has_children, in_expanded, in_depth):
        
        if in_has_children:
            height = in_rect.height() * (3/5.0)
            size = QtCore.QSize(height, height)

            if in_expanded:
                pixmap = down_icon.pixmap(size)

            else:
                pixmap = right_icon.pixmap(size)

            rect = QtCore.QRect(
                in_rect.left(),
                in_rect.top() + (option.rect.height() * (1/5.0)),
                height,
                height
            )

            painter.drawPixmap(rect, pixmap)
            return rect

    def paint(self, painter, option, index):
        rect, selected, expanded, depth, has_children = super(ValueColumnDelegate, self).paint(painter, option, index)

        # タグ描画
        tag_rect = self._draw_tag(painter, option, index, rect, selected, expanded, depth)
        shadow_rect = self._draw_panel_shadow(painter, option, index, tag_rect, selected, expanded, depth)

        # 展開アイコン描画
        self._draw_expand_icon(painter, option, index, rect, selected, has_children, expanded, depth)

style = '''
QTreeView::branch {
        background: palette(base);
}

QHeaderView::section {                          
    color: lightgray;                               
    padding: 0px;                               
    height:20px;                                
    border: 0px solid #567dbc;                  
    border-left:0px;                            
    border-right:0px;                           
    background: #555;
    alignment: right 
}
//

QTreeView::branch:has-siblings:!adjoins-item {
        background: cyan;
}

QTreeView::branch:has-siblings:adjoins-item {
        background: red;
}

QTreeView::branch:!has-children:!has-siblings:adjoins-item {
        background: blue;
}

QTreeView::branch:closed:has-children:has-siblings {
        background: pink;
}

QTreeView::branch:has-children:!has-siblings:closed {
        background: gray;
}

QTreeView::branch:open:has-children:has-siblings {
        background: magenta;
}

QTreeView::branch:open:has-children:!has-siblings {
        background: green;
}
//
'''

class PaneledTreeView(QtWidgets.QTreeView):

    def __init__(self, parent=None):
        super(PaneledTreeView, self).__init__(parent)
        self.show_row_number = True
        self.setIndentation(0) 
        # self.setHeaderHidden(True)
        self.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setStyleSheet(style)
        delegate = PanelItemDelegate()
        self.setItemDelegate(delegate)
        # self.setAutoExpandDelay(2)
        self.setAnimated(True)

    def setModel(self, model):
        super(PaneledTreeView, self).setModel(model)
        self.set_headers()

    def set_headers(self):
        main_column = 0
        header = self.header()
        header.setDefaultAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
        header.setStretchLastSection(False)
        header.setSectionResizeMode(main_column, QtWidgets.QHeaderView.Stretch)

        # ---------------------------------------
        value_delegate = ValueColumnDelegate()
        self.setItemDelegateForColumn(main_column, value_delegate)
        # ---------------------------------------

        for column in range(header.count()):
            if column == main_column:
                continue

            header.setSectionResizeMode(column, QtWidgets.QHeaderView.ResizeToContents)

    # def resizeEvent(self, event):
    #     super(PaneledTreeView, self).resizeEvent(event)

def show():
    win = QtWidgets.QDialog(maya_win)
    vlo = QtWidgets.QVBoxLayout()
    win.setLayout(vlo)

    view = PaneledTreeView()
    model = PanelItemModel()

    model = QtWidgets.QFileSystemModel()
    root_dir = os.path.realpath(os.path.join(__file__, '..', '..', '..'))
    index = model.setRootPath(root_dir)

    # model = QtCore.QStringListModel([str(i) for i in range(100)])
    view.setModel(model)
    view.setRootIndex(index)

    # for i in range(100):
    #     item = PanelItem(AbstractPanelItemData(value=__file__))
    #     model.root_item.add_child(item)

    #     for j in range(2):
    #         item_ = PanelItem(AbstractPanelItemData(value=__file__))
    #         item.add_child(item_)

    #         for k in range(5):
    #             item__ = PanelItem(AbstractPanelItemData(value=__file__))
    #             item_.add_child(item__)

    #             for l in range(3):
    #                 item___ = PanelItem(AbstractPanelItemData(value=__file__))
    #                 item__.add_child(item___)

    vlo.addWidget(view)
    win.resize(400, 200)
    win.show()