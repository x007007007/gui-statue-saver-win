"""
https://docs.microsoft.com/en-us/windows/win32/winmsg/window-features

"""
import ctypes
import json
import logging
import warnings
import datetime
import win32gui
import win32process
from lxml import etree
from lxml import objectify
import time
import warnings

"""
Minimum supported client 	Windows Vista [desktop apps only]
Minimum supported server 	Windows Server 2008 [desktop apps only]
"""
DWM_API = ctypes.WinDLL("dwmapi")

LOGGER = logging.getLogger(__name__)


class WindowInfo(object):

    def __init__(self):
        self._dom = objectify.Element("computer")
        self._windows = objectify.SubElement(self._dom, "windows")
        self._hwnds = objectify.SubElement(self._dom, 'hwnds')
        self._process = objectify.SubElement(self._dom, "process")
        self._tree = etree.ElementTree(self._dom)

    @staticmethod
    def _get_sub_window_detail(shwnd):
        text = win32gui.GetWindowText(shwnd)
        window_rect = win32gui.GetWindowRect(shwnd)
        pos = win32gui.GetWindowPlacement(shwnd)
        menu_item = win32gui.GetMenuItemCount(shwnd)
        client_rect = win32gui.GetClientRect(shwnd)
        return {
            'class': cls_name,
            'pos': pos,
            'win_rect': window_rect,
            'win_place': win32gui.GetWindowPlacement(shwnd),
            'w_visible': win32gui.IsWindowVisible(shwnd),
            'w_enabled': win32gui.IsWindowEnabled(shwnd),
            # 'w_s': win32gui.GetScrollInfo(),
            'cli_rect': client_rect,
            'text': text,
            'menu_item': menu_item,
            # 'label': self._refresh_window_widget_text(shwnd, cls_name)
        }

    def refresh_windows_callback(self, hwnd, stack):
        """

        The IsZoomed and IsIconic functions determine whether a given window is maximized or minimized, respectively.
        The GetWindowPlacement function retrieves the minimized, maximized, and restored positions for the window, and also determines the window's show state.

        :param hwnd:
        :param stack:
        :return:
        """
        tid, pid = win32process.GetWindowThreadProcessId(hwnd)
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        try:
            layer_attr = win32gui.GetLayeredWindowAttributes(hwnd)
            "Retrieves the opacity and transparency color key of a layered window."
        except:
            layer_attr = None
        (
        flags, showCmd, (minposX, minposY), (maxposX, maxposY), (normalposX, normalposY)) = win32gui.GetWindowPlacement(
            hwnd)
        attrs = {
            'hwnd': str(hwnd),
            'is_win_visible': str(win32gui.IsWindowVisible(hwnd)),
            'is_win_enable': str(win32gui.IsWindowEnabled(hwnd)),
            # 'isIconic': str(win32gui.IsIconic(hwnd)),
            'tid': str(tid),
            'pid': str(pid),
            'class': str(win32gui.GetClassName(hwnd)),
            'title': str(win32gui.GetWindowText(hwnd)),
            'left': str(left),
            'top': str(top),
            'right': str(right),
            'bottom': str(bottom),
            'window_placement': json.dumps(),
            'client_rect': json.dumps(win32gui.GetClientRect(hwnd)),
            'layer_attr': json.dumps(layer_attr),
        }
        sub_hwnd_dom = objectify.SubElement(self._windows, "window", **attrs)

    def refresh_windows_only(self):
        self.__window_node_map = {}
        with DataAccessTimeProxy(win_map=self.__window_node_map) as p:
            win32gui.EnumWindows(self.refresh_windows_callback, p.win_map)
        self.__window_node_map_end_time = datetime.datetime.now()
        print("callback ")

    def refresh_windows_map(self):
        def _get_sub_window_children(shwnd, stack: list):
            stack.append(shwnd)

        def _get_sub_window(shwnd, parent):
            attrs = dict(
                hwnd=str(shwnd),
                text=win32gui.GetWindowText(shwnd),
                window_rect=json.dumps(win32gui.GetWindowRect(shwnd)),
                pos=json.dumps(win32gui.GetWindowPlacement(shwnd)),
                client_rect=json.dumps(win32gui.GetClientRect(shwnd)),
            )
            attrs['class'] = str(win32gui.GetClassName(shwnd))
            if (menu_hwnd := win32gui.GetMenu(shwnd)) > 0:
                menu_count = win32gui.GetMenuItemCount(menu_hwnd)
                attrs['menu_count'] = str(menu_count)
                attrs['menu_hwnd'] = str(menu_hwnd)
            sub_win_dom = objectify.SubElement(parent, "subWin", **attrs)
            sub_hwnds = []
            win32gui.EnumChildWindows(shwnd, _get_sub_window_children, sub_hwnds)
            for sub_hwnd in sub_hwnds:
                objectify.SubElement(sub_win_dom, "subWinRef", hwnd=str(sub_hwnd))

        def callback(hwnd, self):
            tid, pid = win32process.GetWindowThreadProcessId(hwnd)
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            try:
                layer_attr = win32gui.GetLayeredWindowAttributes(hwnd)
            except:
                layer_attr = None

            attrs = {
                'hwnd': str(hwnd),
                'is_win_visible': str(win32gui.IsWindowVisible(hwnd)),
                'is_win_enable': str(win32gui.IsWindowEnabled(hwnd)),
                'tid': str(tid),
                'pid': str(pid),
                'class': str(win32gui.GetClassName(hwnd)),
                'title': str(win32gui.GetWindowText(hwnd)),
                'left': str(left),
                'top': str(top),
                'right': str(right),
                'bottom': str(bottom),
                'window_placement': json.dumps(win32gui.GetWindowPlacement(hwnd)),
                'client_rect': json.dumps(win32gui.GetClientRect(hwnd)),
                'layer_attr': json.dumps(layer_attr),
            }
            if (menu_hwnd := win32gui.GetMenu(hwnd)) > 0:
                menu_count = win32gui.GetMenuItemCount(menu_hwnd)
                attrs['menu_count'] = str(menu_count)
                attrs['menu_hwnd'] = str(menu_hwnd)

            sub_hwnd_dom = objectify.SubElement(self._windows, "window", **attrs)
            win32gui.EnumChildWindows(hwnd, _get_sub_window, sub_hwnd_dom)

        win32gui.EnumWindows(callback, self)

    def merge_tree(self):
        for win in self._windows.xpath('.//window'):
            if len(win.xpath("subWin")) > 2:
                print("start")
                print(len(win.xpath("subWin")))

                while len(sub_refs := win.xpath('subWin/subWinRef')) > 0:
                    sub_ref = sub_refs[0]
                    parent = sub_ref.getparent()  # 要替换的结点父结点
                    # 找到 被引用的结点
                    print(parent.tag)
                    if sub_refered_nodes := win.xpath(f'subWin[@hwnd = $hwnd]', hwnd=sub_ref.get("hwnd")):
                        if len(sub_refered_nodes) > 0:
                            sub_refered_node = sub_refered_nodes[0]
                            print(f'move {self._tree.getpath(sub_refered_node)} -> {self._tree.getpath(parent)}')
                            parent.append(sub_refered_node)
                            sub_refered_node.getparent().remove(sub_refered_node)
                            continue
                        else:
                            warnings.warn("no data", UserWarning)
                    sub_refs_hwnd = sub_ref.get("hwnd")
                    warnings.warn(f'hwnd lose data: {sub_refs_hwnd}', UserWarning)
                    parent.remove(sub_ref)
                    objectify.SubElement(parent, "subWinErrRef", hwnd=sub_refs_hwnd)
                print("end", len(win.xpath("subWin")))

    def serilizer(self) -> bytes:
        return etree.tostring(self._dom)


if __name__ == '__main__':
    wi = WindowInfo()
    wi.refresh_windows_only()
