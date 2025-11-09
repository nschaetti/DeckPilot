"""
 ██████╗ ███████╗ ██████╗██╗  ██╗██████╗ ██╗      ██████╗ ██╗████████╗
██╔════╝ ██╔════╝██╔════╝██║  ██║██╔══██╗██║     ██╔═══██╗██║╚══██╔══╝
██║  ███╗█████╗  ██║     ███████║██║  ██║██║     ██║   ██║██║   ██║
██║   ██║██╔══╝  ██║     ██╔══██║██║  ██║██║     ██║   ██║██║   ██║
╚██████╔╝███████╗╚██████╗██║  ██║██████╔╝███████╗╚██████╔╝██║   ██║
 ╚═════╝ ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═════╝ ╚══════╝ ╚═════╝ ╚═╝   ╚═╝

DeckPilot - A customizable interface for your Stream Deck.
Licensed under the GNU General Public License v3.0

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

For a copy of the GNU GPLv3, see <https://www.gnu.org/licenses/>.
"""

# Imports
from typing import Optional
from pathlib import Path

from deckpilot.elements import Panel
from deckpilot.core import DeckRenderer
from deckpilot.utils import Logger


class PomodoroPanel(Panel):
    """
    Pomodoro panel class.
    """

    # Constructor
    def __init__(
            self,
            name: str,
            path: Path,
            renderer: DeckRenderer,
            parent: Optional['Panel'] = None,
            active: bool = False,
            label: Optional[str] = None,
            icon_inactive: str = "default_panel",
            icon_pressed: str = "default_panel_pressed",
            margin_top: Optional[int] = None,
            margin_right: Optional[int] = None,
            margin_bottom: Optional[int] = None,
            margin_left: Optional[int] = None,
            parent_bouton_icon_inactive: str = "parent",
            parent_bouton_icon_pressed: str = "parent_pressed",
            parent_bouton_label: Optional[str] = None,
            parent_bouton_margin_top: Optional[int] = None,
            parent_bouton_margin_right: Optional[int] = None,
            parent_bouton_margin_bottom: Optional[int] = None,
            parent_bouton_margin_left: Optional[int] = None,
            next_page_bouton_icon_inactive: str = "next_page",
            next_page_bouton_icon_pressed: str = "next_page_pressed",
            next_page_bouton_label: Optional[str] = None,
            next_page_bouton_margin_top: Optional[int] = None,
            next_page_bouton_margin_right: Optional[int] = None,
            next_page_bouton_margin_bottom: Optional[int] = None,
            next_page_bouton_margin_left: Optional[int] = None,
            previous_page_bouton_icon_inactive: str = "previous_page",
            previous_page_bouton_icon_pressed: str = "previous_page_pressed",
            previous_page_bouton_label: Optional[str] = None,
            previous_page_bouton_margin_top: Optional[int] = None,
            previous_page_bouton_margin_right: Optional[int] = None,
            previous_page_bouton_margin_bottom: Optional[int] = None,
            previous_page_bouton_margin_left: Optional[int] = None,
            activated_sound: Optional[str] = None,
            alarm_sound: Optional[str] = "alarm",
    ):
        """
        Constructor for the PanelNode class.

        :param name: Name of the panel.
        :type name: str
        :param path: Path to the panel directory.
        :type path: Path
        :param renderer: Deck renderer instance.
        :type renderer: DeckRenderer
        :param parent: Parent panel.
        :type parent: PanelNode
        :param active: Active state.
        :type active: bool
        :param label: Label for the panel.
        :type label: str
        :param icon_inactive: Icon for the inactive state.
        :type icon_inactive: str
        :param icon_pressed: Icon for the active state.
        :type icon_pressed: str
        :param margin_top: Top margin.
        :type margin_top: int
        :param margin_right: Right margin.
        :type margin_right: int
        :param margin_bottom: Bottom margin.
        :type margin_bottom: int
        :param margin_left: Left margin.
        :type margin_left: int
        :param parent_bouton_icon_inactive: Icon for the parent button inactive state.
        :type parent_bouton_icon_inactive: str
        :param parent_bouton_icon_pressed: Icon for the parent button active state.
        :type parent_bouton_icon_pressed: str
        :param parent_bouton_label: Label for the parent button.
        :type parent_bouton_label: str
        :param parent_bouton_margin_top: Top margin for the parent button.
        :type parent_bouton_margin_top: int
        :param parent_bouton_margin_right: Right margin for the parent button.
        :type parent_bouton_margin_right: int
        :param parent_bouton_margin_bottom: Bottom margin for the parent button.
        :type parent_bouton_margin_bottom: int
        :param parent_bouton_margin_left: Left margin for the parent button.
        :type parent_bouton_margin_left: int
        :param next_page_bouton_icon_inactive: Icon for the next page button inactive state.
        :type next_page_bouton_icon_inactive: str
        :param next_page_bouton_icon_pressed: Icon for the next page button active state.
        :type next_page_bouton_icon_pressed: str
        :param next_page_bouton_label: Label for the next page button.
        :type next_page_bouton_label: str
        :param next_page_bouton_margin_top: Top margin for the next page button.
        :type next_page_bouton_margin_top: int
        :param next_page_bouton_margin_right: Right margin for the next page button.
        :type next_page_bouton_margin_right: int
        :param next_page_bouton_margin_bottom: Bottom margin for the next page button.
        :type next_page_bouton_margin_bottom: int
        :param next_page_bouton_margin_left: Left margin for the next page button.
        :type next_page_bouton_margin_left: int
        :param previous_page_bouton_icon_inactive: Icon for the previous page button inactive state.
        :type previous_page_bouton_icon_inactive: str
        :param previous_page_bouton_icon_pressed: Icon for the previous page button active state.
        :type previous_page_bouton_icon_pressed: str
        :param previous_page_bouton_label: Label for the previous page button.
        :type previous_page_bouton_label: str
        :param previous_page_bouton_margin_top: Top margin for the previous page button.
        :type previous_page_bouton_margin_top: int
        :param previous_page_bouton_margin_right: Right margin for the previous page button.
        :type previous_page_bouton_margin_right: int
        :param previous_page_bouton_margin_bottom: Bottom margin for the previous page button.
        :type previous_page_bouton_margin_bottom: int
        :param previous_page_bouton_margin_left: Left margin for the previous page button.
        :type previous_page_bouton_margin_left: int
        :param activated_sound: Sound to play when the countdown is activated.
        :type activated_sound: str
        :param alarm_sound: Sound to play when the countdown is finished.
        :type alarm_sound: str
        """
        super().__init__(
            name=name,
            path=path,
            renderer=renderer,
            parent=parent,
            active=active,
            label=label,
            icon_inactive=icon_inactive,
            icon_pressed=icon_pressed,
            margin_top=margin_top,
            margin_right=margin_right,
            margin_bottom=margin_bottom,
            margin_left=margin_left,
            parent_bouton_icon_inactive=parent_bouton_icon_inactive,
            parent_bouton_icon_pressed=parent_bouton_icon_pressed,
            parent_bouton_label=parent_bouton_label,
            parent_bouton_margin_top=parent_bouton_margin_top,
            parent_bouton_margin_right=parent_bouton_margin_right,
            parent_bouton_margin_bottom=parent_bouton_margin_bottom,
            parent_bouton_margin_left=parent_bouton_margin_left,
            next_page_bouton_icon_inactive=next_page_bouton_icon_inactive,
            next_page_bouton_icon_pressed=next_page_bouton_icon_pressed,
            next_page_bouton_label=next_page_bouton_label,
            next_page_bouton_margin_top=next_page_bouton_margin_top,
            next_page_bouton_margin_right=next_page_bouton_margin_right,
            next_page_bouton_margin_bottom=next_page_bouton_margin_bottom,
            next_page_bouton_margin_left=next_page_bouton_margin_left,
            previous_page_bouton_icon_inactive=previous_page_bouton_icon_inactive,
            previous_page_bouton_icon_pressed=previous_page_bouton_icon_pressed,
            previous_page_bouton_label=previous_page_bouton_label,
            previous_page_bouton_margin_top=previous_page_bouton_margin_top,
            previous_page_bouton_margin_right=previous_page_bouton_margin_right,
            previous_page_bouton_margin_bottom=previous_page_bouton_margin_bottom,
            previous_page_bouton_margin_left=previous_page_bouton_margin_left,
            activated_sound=activated_sound
        )

        # Queue of countdowns
        self.queue = []
        self.current_countdown = None

        # Alarm sound
        self.alarm_sound = alarm_sound
    # end __init__

    # region PUBLIC

    def add_countdown(self, duration: int):
        """
        Add a countdown.

        Args:
            duration (int): Duration of the countdown in seconds.
        """
        # Debug
        Logger.inst().debug(f"Adding countdown: {duration} seconds")

        # Add countdown to queue
        self.queue.append(duration)

        # Start countdown if not already running
        self._start()
    # end add_countdown

    # Pause countdown
    def pause_countdown(self):
        """
        Pause the current countdown.
        """
        # Debug
        Logger.inst().debug(f"Pause countdown")

        if self.current_countdown:
            self.dispatch(source=self, data={'action': "pause"})
        # end if
    # end pause_countdown

    # Stop countdown
    def stop_countdown(self, play_sound: bool = False):
        """
        Stop the current countdown.

        Args:
            play_sound (bool): Play sound when stopping the countdown.
        """
        # Debug
        Logger.inst().debug(f"Stop countdown")

        # If there is a countdown running, stop it
        if self.current_countdown:
            # Dispatch stop event, and reset countdown
            self.dispatch(source=self, data={'action': "stop"})
            self.current_countdown = None

            # If there are more countdowns in the queue, start the next one
            self._start()

            # Update countdown states
            self._update_countdown_states()

            # Play sound if requested
            if play_sound and self.alarm_sound:
                self.dispatch(source=self, data={'action': "alarm"})
                self.play_sound(self.alarm_sound)
            # end if
        # end if
    # end stop_countdown

    # endregion PUBLIC

    # region PRIVATE

    # Update countdowns states
    def _update_countdown_states(self):
        """
        Update the countdown states.
        """
        # Debug
        Logger.inst().debug(f"Update countdowns")

        # If there is a countdown running, update it
        if self.current_countdown:
            self.dispatch(source=self, data={'action': "update", "duration": self.current_countdown})
            if len(self.queue) > 0:
                self.dispatch(source=self, data={'action': "next", "duration": self.queue[0]})
            # end if
        else:
            self.dispatch(source=self, data={'action': "update", "duration": -1})
        # end if
    # end _update_countdown_states

    def _start(self):
        """
        Start the countdown.
        """
        # There is a countdown in the queue, and no countdown is currently running
        if len(self.queue) > 0 and not self.current_countdown:
            duration = self.queue.pop(0)
            self.current_countdown = duration
            self.dispatch(source=self, data={'action': "start", "duration": duration})
        # end if
        self._update_countdown_states()
    # end _start

    # endregion PRIVATE

# end PomodoroPanel
