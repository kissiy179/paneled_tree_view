# -*- coding: utf-8 -*-
import os
from mayaqt import QtCore, QtGui, QtWidgets, maya_win, qt_cud_colors
import paneled_tree_view; reload(paneled_tree_view)

def show():
    win = QtWidgets.QDialog(maya_win)
    vlo = QtWidgets.QVBoxLayout()
    win.setLayout(vlo)

    view = paneled_tree_view.PaneledTreeView()
    model = paneled_tree_view.PanelItemModel()

    model = QtWidgets.QFileSystemModel()
    root_dir = os.path.realpath(os.path.join(__file__, '..', '..'))
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
    win.resize(600, 400)
    win.show()