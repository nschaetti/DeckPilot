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
import json
# Imports
from typing import Any, Optional, Callable
import threading
from enum import Enum
from pathlib import Path
import obsws_python as obs
import obsws_python.error as obs_error
import websocket._exceptions as ws_exceptions
from datetime import datetime, timedelta

from deckpilot.elements import Panel, Item
from deckpilot.utils import Logger
from deckpilot.core import KeyDisplay, DeckRenderer
from deckpilot.comm import context


# Event names as Enum
class OBSEvent(str, Enum):
    SCENE_CREATED = "on_scene_created"
    SCENE_REMOVED = "on_scene_removed"
    SCENE_NAME_CHANGED = "on_scene_name_changed"
    SCENE_LIST_CHANGED = "on_scene_list_changed"
    CURRENT_PROGRAM_SCENE_CHANGED = "on_current_program_scene_changed"
    CURRENT_PREVIEW_SCENE_CHANGED = "on_current_preview_scene_changed"
    STREAM_STATE_CHANGED = "on_stream_state_changed"
    RECORD_STATE_CHANGED = "on_record_state_changed"
    INPUT_ACTIVE_STATE_CHANGED = "on_input_active_state_changed"
    INPUT_SHOW_STATE_CHANGED = "on_input_show_state_changed"
    INPUT_MUTE_STATE_CHANGED = "on_input_mute_state_changed"
# end OBSEvent


# A scene object
class OBSScene:
    """
    OBS Scene class to manage the scene.
    """

    def __init__(
            self,
            index: int,
            name: str
    ):
        """
        Constructor

        :param index: the index of the scene
        :type index: int
        :param name: the name of the scene
        :type name: str
        """
        # Index and name
        self.index = index
        self.name = name
        self.current = False
        self.current_preview = False
    # end __init__

    # Set current
    def set_current(
            self,
            value: bool
    ):
        """
        Set current scene

        :param value: the value
        :type value: bool
        """
        # Set current
        self.current = value

        # Log
        Logger.inst().info(f"Set current scene: {self.name}={self.current}")
    # end set_current

    # Set current preview
    def set_current_preview(
            self,
            value: bool
    ):
        """
        Set current preview scene

        :param value: the value
        :type value: bool
        """
        # Set current
        self.current_preview = value

        # Log
        Logger.inst().info(f"Set current preview scene: {self.name}={self.current_preview}")
    # end set_current_preview

# OBSScene


# OBS Connector
class OBSConnector:
    """
    OBS Connector class to manage the connection to the OBS server.
    """

    # Constructor
    def __init__(
            self,
            host: str,
            port: int,
            password: str
    ):
        """
        Constructor

        :param host: the host of the OBS server
        :type host: str
        :param port: the port of the OBS server
        :type port: int
        :param password: the password of the OBS server
        :type password: str
        """
        # Host and port
        self.host = host
        self.port = port
        self.password = password

        # Client & scenes
        self.client = None
        self.event_client = None
        self._scenes = {}

        # States
        self.streaming = False
        self.recording = False
        self.recording_paused = False

        # State info
        self.recording_path = ""

        # Inputs
        self.inputs = {}

        # Current scene
        self.current_program_scene = None
        self.current_preview_scene = None

        # Callbacks
        self.callbacks = {}

        # Lock
        self._lock = threading.RLock()
    # end __init__

    # region PROPERTIES

    @property
    def connected(self):
        return self.client is not None
    # end connected

    # Scenes
    @property
    def scenes(self):
        with self._lock:
            return self._scenes
        # end with
    # end scenes

    # Event list
    @property
    def event_list(self):
        """
        Event list
        """
        return [
            event_name for event_name in dir(self)
            if event_name.startswith("on_") and callable(getattr(self, event_name))
        ]
    # end event_list

    @property
    def is_streaming(self):
        """
        Is streaming
        """
        return self.streaming
    # end is_streaming

    @property
    def is_recording(self):
        """
        Is recording
        """
        return self.recording
    # end is_recording

    @property
    def is_recording_paused(self):
        """
        Is recording paused
        """
        return self.recording_paused
    # end is_recording_paused

    # endregion PROPERTIES

    # region PUBLIC

    # Connect
    def connect(
            self,
            timeout: int = 3
    ):
        """
        Try to connect to the OBS server.
        Warning: this method will reset callbacks, you have to register them again.

        Args:
        - timeout: int - the timeout in seconds (default: 3)
        """
        # Log
        Logger.inst().info(f"Connecting to OBS server: {self.host}:{self.port}")

        # Connect
        self.client = obs.ReqClient(
            host=self.host,
            port=self.port,
            password=self.password,
            timeout=timeout
        )

        # Log
        Logger.inst().info(f"Connected to OBS server: {self.host}:{self.port}")
        Logger.inst().info(f"Connecting event client to OBS server: {self.host}:{self.port}")

        # Event client
        self.event_client = obs.EventClient(
            host=self.host,
            port=self.port,
            password=self.password,
            timeout=timeout
        )

        # Initialize
        Logger.inst().debug(f"Initializing OBS client: {self.host}:{self.port}")
        self._initialize()
    # end connect

    # Get input list
    def get_input_list(self, kind=None):
        """
        Get input list

        Args:
        - kind: str - the kind of input (default: None)

        Returns:
        - list: the list of inputs
        """
        return self.client.get_input_list(kind=kind)
    # end get_input_list

    # Get stats
    def get_stats(self):
        """
        Get stats

        Returns:
        - dict: the stats
        """
        with self._lock:
            return self.client.get_stats()
        # end with lock
    # end get_stats

    # Get input kind list
    def get_input_kind_list(self):
        """
        Get input kind list

        Args: None

        Returns:
        - list: the list of input kinds
        """
        with self._lock:
            return self.client.get_input_kind_list(unversioned=True)
        # end with lock
    # end get_input_kind_list

    # Get special inputs
    def get_special_inputs(self):
        """
        Get special inputs

        Args: None

        Returns:
        - list: the list of special inputs
        """
        with self._lock:
            return self.client.get_special_inputs()
        # end with
    # end get_special_inputs

    # Get input mute
    def get_input_mute(self, name: str) -> bool:
        """
        Get input mute

        Args:
        - name: str - the name of the input

        Returns:
        - bool: the mute state
        """
        with self._lock:
            return self.client.get_input_mute(name=name)
        # end with
    # end get_input_mute

    # Toogle input mute
    def toggle_input_mute(self, name: str):
        """
        Toggle input mute

        Args:
        - name: str - the name of the input
        """
        # Toggle input mute
        with self._lock:
            self.client.toggle_input_mute(name=name)
        # end with lock
    # end toggle_input_mute

    # Set input mute
    def set_input_mute(self, name: str, muted: bool):
        """
        Set input mute

        Args:
        - name: str - Name of the input to set the mute state of
        - muted: bool - Whether to mute the input or not
        """
        with self._lock:
            # Set input mute
            self.client.set_input_mute(name=name, muted=muted)
        # end with
    # end set_input_mute

    # Get input volume
    def get_input_volume(self, name: str):
        """
        Gets the current volume setting of an input.

        Args:
        - name: str - Name of the input to get the volume of

        Returns:
        - float: Volume setting in dB  (>= -100, <= 26)
        """
        with self._lock:
            return self.client.get_input_volume(name=name)
        # end with
    # end get_input_volume

    # Set input volume
    def set_input_volume(self, name: str, volume_mul: int, volume_db: int):
        """
        Set input volume

        Args:
        - name: str - Name of the input to set the volume of
        - volume_mul: int - Volume setting in mul (>= 0, <= 20)
        - volume_db: int - Volume setting in dB  (>= -100, <= 26)
        """
        with self._lock:
            # Set input volume
            self.client.set_input_volume(name=name, volume_mul=volume_mul, volume_db=volume_db)
        # end with
    # end set_input_volume

    # Scene list
    def scene_list(
            self
    ):
        """
        Scene list

        Args: None

        Returns:
        - list: the list of scenes
        """
        with self._lock:
            return list(self.scenes.keys())
        # end with
    # end scene_list

    # Get input state
    def get_input(
            self,
            input_name: str
    ):
        """
        Get input state

        :param input_name: the name of the input
        :type input_name: str
        :return: the state of the input
        :rtype: bool
        """
        with self._lock:
            if input_name in self.inputs:
                return self.inputs[input_name]
            else:
                raise ValueError(f"Input '{input_name}' not found")
            # end if
        # end with lock
    # end get_input

    # Get scene
    def get_scene(
            self,
            scene_name: str
    ):
        """
        Get scene

        Args:
        - scene_name: str - the name of the scene

        Returns:
        - Scene: the scene object
        """
        with self._lock:
            if scene_name in self._scenes:
                return self._scenes.get(scene_name)
            else:
                raise ValueError(f"Scene '{scene_name}' not found")
            # end if
        # end with
    # end get_scene

    # Register event
    def register_event(
            self,
            event: OBSEvent,
            callback: Callable
    ):
        """
        Register event

        Args:
        - event_name: str - the name of the event
        - callback: Callable - the callbac
        """
        # Check that the event is valid
        if event not in self.callbacks:
            self.callbacks[event] = []
        # end if

        # Register the callback
        self.callbacks[event].append(callback)
    # endregion PUBLIC

    # Change current scene
    def change_scene(self, scene_name: str):
        """
        Change scene

        Args:
        - scene_name: str - the name of the scene
        """
        with self._lock:
            # Change scene
            self.client.set_current_program_scene(scene_name)
        # end with
    # end change_scene

    # Start recording
    def start_recording(self):
        """
        Start recording
        """
        with self._lock:
            # Start recording
            self.client.start_record()
        # end with
    # end start_recording

    # Stop recording
    def stop_recording(self):
        """
        Stop recording
        """
        with self._lock:
            # Stop recording
            self.client.stop_record()
        # end with
    # end stop_recording

    # Pause recording
    def pause_recording(self):
        """
        Pause recording
        """
        with self._lock:
            # Pause recording
            self.client.pause_record()
        # end with
    # end pause_recording

    # Resume recording
    def resume_recording(self):
        """
        Resume recording
        """
        with self._lock:
            # Resume recording
            self.client.resume_record()
        # end with
    # end resume_recording

    # Start streaming
    def start_streaming(self):
        """
        Start streaming
        """
        with self._lock:
            # Start streaming
            self.client.start_stream()
        # end with
    # end start_streaming

    # Stop streaming
    def stop_streaming(self):
        """
        Stop streaming
        """
        with self._lock:
            # Stop streaming
            self.client.stop_stream()
        # end with
    # end stop_streaming

    # region PRIVATE

    # Initialize (get all scene and status)
    def _initialize(self):
        """
        Initialize

        Args: None

        Returns: None
        """
        with self._lock:
            # Initialize states
            Logger.inst().debug("Initializing states")
            self._initialize_states()

            # Initialize inputs
            Logger.inst().debug("Initializing inputs")
            self._initialize_inputs()

            # Scenes
            Logger.inst().debug("Initializing scenes")
            self._initialize_scenes()

            # Initialize callbacks
            Logger.inst().debug("Initializing callbacks")
            self._initialize_callbacks()
        # end lock
    # end _initialize

    # Initialize inputs
    def _initialize_inputs(self):
        """
        Initialize inputs
        """
        # Inputs
        input_list = self.client.get_input_list().inputs

        # Create each object
        for input in input_list:
            # Input info
            input_kind = input['inputKind']
            input_name = input['inputName']
            unversioned_input_kind = input['unversionedInputKind']

            # Create if not in
            if input_name not in self.inputs:
                self.inputs[input_name] = {
                    "kind": input_kind,
                    "name": input_name,
                    "unversioned_kind": unversioned_input_kind
                }
            # end if

            # Get input settings
            input_settings = self.client.get_input_settings(input_name).input_settings
            self.inputs[input_name]["settings"] = input_settings
        # end for

        # Log
        Logger.inst().info(f"OBS Inputs listed: {self.inputs}")
    # end _initialize_inputs

    # Initialize scenes
    def _initialize_scenes(self):
        """
        Initialize scenes

        Args: None

        Returns: None
        """
        # Update scene list
        Logger.inst().debug("Updating scene list")
        self._update_scene_list()

        # Update current scene
        Logger.inst().debug("Updating current scene")
        self._update_current_scene()

        # Log
        Logger.inst().info(f"OBS Scenes listed: {self._scenes}")
    # end _initialize_scenes

    # Initialize states
    def _initialize_states(self):
        """
        Initialize states
        """
        # Streaming
        self.streaming = self.client.get_stream_status().output_active

        # Recording
        self.recording = self.client.get_record_status().output_active
        self.recording_paused = self.client.get_record_status().output_paused

        # Log
        Logger.inst().info(
            f"OBS states: streaming={self.streaming}, recording={self.recording}, "
            f"recording_paused={self.recording_paused}"
        )
    # end _initialize_states

    # Initialize callbacks
    def _initialize_callbacks(self):
        """
        Initialize callbacks

        Args: None

        Returns: None
        """
        # Get all event methods
        event_func_names = [m_name for m_name in dir(self) if m_name.startswith("on_") and callable(getattr(self, m_name))]

        # Register all events
        for event_name in event_func_names:
            self.callbacks[event_name] = []
            self.event_client.callback.register(getattr(self, event_name))
        # end for

        # Returns a list of currently registered events
        Logger.inst().info(f"Registered callbacks: {self.event_client.callback.get()}")
    # end _initialize_callbacks

    # Update scene list
    def _update_scene_list(self):
        """
        Update scene list
        """
        with self._lock:
            # Scenes
            scene_list = self.client.get_scene_list().scenes

            # Create each object
            for scene in scene_list:
                # Scene info
                scene_name = scene['sceneName']
                scene_index = scene['sceneIndex']

                # Create if not in
                if scene_name not in self._scenes:
                    self._scenes[scene_name] = OBSScene(
                        index=scene_index,
                        name=scene_name
                    )
                else:
                    self._scenes[scene_name].index = scene_index
                    self._scenes[scene_name].name = scene_name
                # end if
            # end for
        # end lock
    # end _update_scene_list

    # Update current scene
    def _update_current_scene(self):
        """
        Update current scene
        """
        with self._lock:
            # Current scene
            current_program_scene_name = self.client.get_current_program_scene().current_program_scene_name

            # Log
            Logger.inst().debug(f"Current program scene: {current_program_scene_name}")

            # Current preview scene
            try:
                current_preview_scene_name = self.client.get_current_preview_scene().current_preview_scene_name
            except obs_error.OBSSDKRequestError as e:
                if e.code == 506:
                    Logger.inst().warning("Studio Mode is not activated in OBS.")
                else:
                    Logger.inst().warning(f"Get current preview scene failed: code={e.code}")
                # end if
                current_preview_scene_name = None
            except Exception as e:
                Logger.inst().warning(f"Unexpected error while getting preview scene: {e}")
                current_preview_scene_name = None
            # end try

            # Log
            Logger.inst().debug(f"Current preview scene: {current_preview_scene_name}")

            # Update program scene
            if current_program_scene_name in self._scenes:
                # Set current scene
                self.current_program_scene = self._scenes[current_program_scene_name]
                self._scenes[current_program_scene_name].set_current(True)
                for scene_name, scene in self._scenes.items():
                    if scene_name != current_program_scene_name:
                        scene.set_current(False)
                    # end if
                # end for
            # end if

            # Update preview scene
            if current_preview_scene_name is not None and current_preview_scene_name in self._scenes:
                # Set current scene
                self.current_preview_scene = self._scenes[current_preview_scene_name]
                self._scenes[current_preview_scene_name].set_current_preview(True)
                for scene_name, scene in self._scenes.items():
                    if scene_name != current_preview_scene_name:
                        scene.set_current_preview(False)
                    # end if
                # end for
            # end if
        # end with lock
    # end _update_current_scene

    # Trigger callbacks
    def _trigger_callbacks(
            self,
            event_name: str,
            data
    ):
        """
        Trigger callbacks

        :param event_name: the name of the event
        :type event_name: str
        :param data: the data to pass to the callback
        :type data: Any
        """
        # Callbacks
        for callback in self.callbacks[event_name]:
            callback(data)
        # end for
    # end _trigger_callbacks

    # endregion PRIVATE

    # region EVENTS

    # Scene created
    def on_scene_created(
            self,
            data
    ):
        """
        On scene created

        :param data: the message
        :type data: Any
        """
        # Attrs: is_group, scene_name
        Logger.inst().info(f"Scene created: is_group={data.is_group}, scene_name={data.scene_name}")

        # Update scene list
        self._update_scene_list()

        # Callbacks
        self._trigger_callbacks(OBSEvent.SCENE_CREATED, data)
    # end on_scene_created

    # Scene removed
    def on_scene_removed(
            self,
            data
    ):
        """
        On scene removed

        :param data: the message
        :type data: Any
        """
        # Attrs: is_group, scene_name
        Logger.inst().info(f"Scene removed: is_group={data.is_group}, scene_name={data.scene_name}")

        # Update scene list
        self._update_scene_list()

        # Callbacks
        self._trigger_callbacks(OBSEvent.SCENE_REMOVED, data)
    # end on_scene_removed

    # Scene name changed
    def on_scene_name_changed(
            self,
            data
    ):
        """
        On scene name changed

        :param data: the message
        :type data: Any
        """
        # Attrs: new_name, old_name
        Logger.inst().info(
            f"Scene name changed: scene_uuid={data.scene_uuid}, old_scene_name={data.old_scene_name}, "
            f"scene_name={data.scene_name}"
        )

        # Update list
        self._scenes[data.scene_name] = self._scenes.pop(data.old_scene_name)

        # Update scene list
        self._update_scene_list()

        # Callbacks
        self._trigger_callbacks(OBSEvent.SCENE_NAME_CHANGED, data)
    # end on_scene_name_changed

    # On scene list changed
    def on_scene_list_changed(
            self,
            data
    ):
        """
        On scene list changed

        :param data: the message
        :type data: Any
        """
        # Attrs: scenes
        Logger.inst().info(f"Scene list changed: scenes={data.scenes}")

        # Update scene list
        self._update_scene_list()

        # Callbacks
        self._trigger_callbacks(OBSEvent.SCENE_LIST_CHANGED, data)
    # end on_scene_list_changed

    # On current program scene changed
    def on_current_program_scene_changed(
            self,
            data
    ):
        """
        On current program scene changed

        :param data: the message
        :type data: Any
        """
        # Attrs: current_name
        Logger.inst().info(f"Current program scene changed: attrs={data.attrs()}")
        Logger.inst().info(f"Current program scene changed: scene_name={data.scene_name}")

        # Update current scene
        self._update_current_scene()

        # Callbacks
        self._trigger_callbacks(OBSEvent.CURRENT_PROGRAM_SCENE_CHANGED, data)

    # end on_current_program_scene_changed

    # On current preview scene changed
    def on_current_preview_scene_changed(
            self,
            data
    ):
        """
        On current preview scene changed

        :param data: the message
        :type data: Any
        """
        # Attrs: current_name
        Logger.inst().info(f"Current preview scene changed: attrs={data.attrs()}")
        Logger.inst().info(f"Current preview scene changed: scene_name={data.scene_name}")

        # Update current scene
        self._update_current_scene()

        # Callbacks
        self._trigger_callbacks(OBSEvent.CURRENT_PREVIEW_SCENE_CHANGED, data)
    # end on_current_preview_scene_changed

    # On stream state changed
    def on_stream_state_changed(
            self,
            data
    ):
        """
        On stream state changed

        :param data: the message
        :type data: Any
        """
        # Attrs: streaming, recording
        Logger.inst().info(f"Stream state changed: attrs={data.attrs()}")
        Logger.inst().info(
            f"Stream state changed: "
            f"output_active={data.output_active}, "
            f"output_state={data.output_state}"
        )

        # Update recording state
        self.streaming = data.output_active

        # Callbacks
        self._trigger_callbacks(OBSEvent.STREAM_STATE_CHANGED, data)
    # end on_stream_state_changed

    # On record state changed
    def on_record_state_changed(
            self,
            data
    ):
        """
        On record state changed

        :param data: the message
        :type data: Any
        """
        # Attrs: streaming, recording
        Logger.inst().info(f"Record state changed: attrs={data.attrs()}")
        Logger.inst().info(
            f"Record state changed: "
            f"output_active={data.output_active}, "
            f"output_path={data.output_path}, "
            f"output_state={data.output_state}"
        )

        # Update recording state
        self.recording = data.output_active
        self.recording_path = data.output_path

        # Paused
        if data.output_state == "OBS_WEBSOCKET_OUTPUT_PAUSED":
            self.recording_paused = True
        else:
            self.recording_paused = False
        # end if

        # Log
        Logger.inst().debug(f"Recording state: {self.recording}, paused={self.recording_paused}")
        Logger.inst().debug(f"Recording path: {self.recording_path}")

        # Callbacks
        self._trigger_callbacks(OBSEvent.RECORD_STATE_CHANGED, data)
    # end on_record_state_changed

    # On input active state changed
    def on_input_active_state_changed(
            self,
            data
    ):
        """
        On input active state changed

        :param data: the message
        :type data: Any
        """
        # Attrs: input_name, active
        Logger.inst().info(f"Input active state changed: attrs={data.attrs()}")

        # Callbacks
        self._trigger_callbacks(OBSEvent.INPUT_ACTIVE_STATE_CHANGED, data)
    # end on_input_active_state_changed

    # On input show state changed
    def on_input_show_state_changed(
            self,
            data
    ):
        """
        On input show state changed

        :param data: the message
        :type data: Any
        """
        # Attrs: input_name, show
        Logger.inst().info(f"Input show state changed: attrs={data.attrs()}")

        # Callbacks
        self._trigger_callbacks(OBSEvent.INPUT_SHOW_STATE_CHANGED, data)
    # end on_input_show_state_changed

    # On input mute state changed
    def on_input_mute_state_changed(
            self,
            data
    ):
        """
        On input mute state changed

        :param data: the message
        :type data: Any
        """
        # Attributes
        input_muted = data.input_muted
        input_name = data.input_name
        input_uuid = data.input_uuid

        # Attrs: input_name, muted
        Logger.inst().info(f"Input mute state changed: input_muted={input_muted}, input_name={input_name}, input_uuid={input_uuid}")
        print(dir(data))
        # Callbacks
        self._trigger_callbacks(
            OBSEvent.INPUT_MUTE_STATE_CHANGED,
            data
        )
    # end on_input_mute_state_changed

    # endregion EVENTS

    # region STRING

    # To string
    def __str__(self):
        """
        To string

        Return:
        - str: the string representation
        """
        # List of scenes
        scenes = "\n\t\t".join([str(scene) for scene in self._scenes.values()])

        # Return
        return f"OBSConnector(host={self.host}, port={self.port}, connected={self.connected})\n\tScenes:\n{scenes})"
    # end __str__

    # To repr
    def __repr__(self):
        """
        To repr

        Return:
        - str: the string representation
        """
        # List of scenes
        scenes = "\n\t\t".join([str(scene) for scene in self._scenes.values()])

        return f"OBSConnector(host={self.host}, port={self.port}, connected={self.connected})\n\tScenes:\n{scenes}"
    # end __repr__

    # endregion STRING

# end OBSConnector


# Panel
class OBSPanel(Panel):
    """
    OBSPanel class represents a panel in the Stream Deck application.
    It inherits from the Item class and provides additional functionality
    specific to OBS panels.
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
            activated_sound: Optional[str] = None
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
        :param activated_sound: Sound to play when the panel is activated.
        :type activated_sound: str
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
        # Log
        Logger.inst().info(f"OBSPanel {name} created!")

        # OBS configuration
        if 'obs' in context.config:
            self.obs_host = context.config['obs'].get("obs_host", "localhost")
            self.obs_port = context.config['obs'].get("obs_port", 4444)
            self.obs_password = context.config['obs'].get("obs_password", "1234")
        else:
            self.obs_host = "localhost"
            self.obs_port = 4444
            self.obs_password = "1234"
        # end if

        # Log
        Logger.inst().info(f"OBS configuration: host={self.obs_host}, port={self.obs_port}")
        Logger.inst().debug("Creating OBSConnector")

        # Create OBS Connector
        self.obs_connector = OBSConnector(
            host=self.obs_host,
            port=self.obs_port,
            password=self.obs_password
        )

        # Log
        Logger.inst().debug(f"OBSConnector: {self.obs_connector}")

        # Connect to OBS
        self.last_connection_attempt = datetime.now()
        self.obs_connected = False
        self._connect_obs()
    # end __init__

    # region PUBLIC

    # Is OBS recording
    def is_recording(
            self
    ):
        """
        Is OBS recording

        :return: the recording state
        :rtype: bool
        """
        return self.obs_connector.is_recording
    # end is_recording

    # Is OBS streaming
    def is_streaming(
            self
    ):
        """
        Is OBS streaming

        :return: the streaming state
        :rtype: bool
        """
        return self.obs_connector.is_streaming
    # end is_streaming

    # Is OBS recording paused
    def is_recording_paused(
            self
    ):
        """
        Is OBS recording paused

        :return: the recording paused state
        :rtype: bool
        """
        return self.obs_connector.is_recording_paused
    # end is_recording_paused

    # Start OBS recording
    def start_recording(
            self
    ):
        """
        Start OBS recording
        """
        self.obs_connector.start_recording()
    # end start_recording

    # Stop OBS recording
    def stop_recording(
            self
    ):
        """
        Stop OBS recording
        """
        self.obs_connector.stop_recording()
    # end stop_recording

    # Pause OBS recording
    def pause_recording(
            self
    ):
        """
        Pause OBS recording
        """
        self.obs_connector.pause_recording()
    # end pause_recording

    # Resume OBS recording
    def resume_recording(
            self
    ):
        """
        Resume OBS recording
        """
        self.obs_connector.resume_recording()
    # end resume_recording

    # Start OBS streaming
    def start_streaming(
            self
    ):
        """
        Start OBS streaming
        """
        self.obs_connector.start_streaming()
    # end start_streaming

    # Stop OBS streaming
    def stop_streaming(
            self
    ):
        """
        Stop OBS streaming
        """
        self.obs_connector.stop_streaming()
    # end stop_streaming

    # Change scene
    def change_scene(
            self,
            scene_name: str
    ):
        """
        Change scene

        :param scene_name: the name of the scene
        :type scene_name: str
        """
        self.obs_connector.change_scene(scene_name)
    # end change_scene

    # Get scene
    def get_scene(
            self,
            scene_name: str
    ):
        """
        Get scene

        :param scene_name: the name of the scene
        :type scene_name: str
        :return: the scene object
        :rtype: OBSScene
        """
        return self.obs_connector.get_scene(scene_name)
    # end get_scene

    # Get input
    def get_input(
            self,
            input_name: str
    ):
        """
        Get input

        :param input_name: the name of the input
        :type input_name: str
        :return: the state of the input
        :rtype: bool
        """
        return self.obs_connector.get_input(input_name)
    # end get_input

    # Get special inputs
    def get_special_inputs(
            self
    ):
        """
        Get special inputs

        :return: the special inputs
        :rtype: OBSSpecialInputs
        """
        special_inputs = self.obs_connector.get_special_inputs()
        return {
            "desktop1": special_inputs.desktop1,
            "desktop2": special_inputs.desktop2,
            "mic1": special_inputs.mic1,
            "mic2": special_inputs.mic2,
            "mic3": special_inputs.mic3,
            "mic4": special_inputs.mic4
        }
    # end get_special_inputs

    # Get special input
    def get_special_input(
            self,
            input_name: str
    ):
        """
        Get special input

        :param input_name: the name of the input
        :type input_name: str
        :return: the state of the input
        :rtype: bool
        """
        special_inputs = self.obs_connector.get_special_inputs()
        return getattr(special_inputs, input_name, None)
    # end get_special_input

    # Get input mute state
    def get_input_mute_state(
            self,
            input_name: str
    ):
        """
        Get input mute state

        :param input_name: the name of the input
        :type input_name: str
        :return: the state of the input
        :rtype: bool
        """
        return self.obs_connector.get_input_mute(input_name)
    # end get_input_mute_state

    # Toggle input mute
    def toggle_input_mute(
            self,
            input_name: str
    ):
        """
        Toggle input mute

        :param input_name: the name of the input
        :type input_name: str
        """
        self.obs_connector.toggle_input_mute(input_name)
    # end toggle_input_mute

    # Get scene list
    def get_scene_list(
            self
    ):
        """
        Get scene list

        :return: the list of scenes
        :rtype: list
        """
        return self.obs_connector.scene_list()
    # end get_scene_list

    # Get current program scene
    def get_current_program_scene(
            self
    ):
        """
        Get current program scene

        :return: the current program scene
        :rtype: OBSScene
        """
        return self.obs_connector.current_program_scene
    # end get_current_program_scene

    # Get current preview scene
    def get_current_preview_scene(
            self
    ):
        """
        Get current preview scene

        :return: the current preview scene
        :rtype: OBSScene
        """
        return self.obs_connector.current_preview_scene
    # end get_current_preview_scene

    # Get streaming state
    def get_streaming_state(
            self
    ):
        """
        Get streaming state

        :return: the streaming state
        :rtype: bool
        """
        return self.obs_connector.is_streaming
    # end get_streaming_state

    # Get recording state
    def get_recording_state(
            self
    ):
        """
        Get recording state

        :return: the recording state
        :rtype: bool
        """
        return self.obs_connector.is_recording
    # end get_recording_state

    # Get recording paused state
    def get_recording_paused_state(
            self
    ):
        """
        Get recording paused state

        :return: the recording paused state
        :rtype: bool
        """
        return self.obs_connector.is_recording_paused
    # end get_recording_paused_state

    # endregion PUBLIC

    # region PRIVATE

    # Show debug information (OBS information)
    def _show_debug_info(self):
        """
        Show debug information (OBS information)
        """
        # Log
        Logger.inst().info(f"Scene list: {self.obs_connector.scene_list()}")
        Logger.inst().info(f"Input list: {self.obs_connector.get_input_list().inputs}")
        Logger.inst().info(f"Input lind list: {self.obs_connector.get_input_kind_list().input_kinds}")

        # Special inputs
        special_inputs = self.obs_connector.get_special_inputs()
        Logger.inst().info(f"Special desktop1 input: {special_inputs.desktop1}")
        Logger.inst().info(f"Special desktop2 input: {special_inputs.desktop2}")
        Logger.inst().info(f"Special mic1 input: {special_inputs.mic1}")
        Logger.inst().info(f"Special mic2 input: {special_inputs.mic2}")
        Logger.inst().info(f"Special mic3 input: {special_inputs.mic3}")
        Logger.inst().info(f"Special mic4 input: {special_inputs.mic4}")

        # Get input mute of each input
        for obs_input in self.obs_connector.get_input_list().inputs:
            if obs_input['inputKind'] in ['alsa_input_capture', 'jack_output_capture', 'pulse_input_capture',
                                          'pulse_output_capture']:
                # Get input mute
                input_mute = self.obs_connector.get_input_mute(name=obs_input['inputName'])

                if input_mute:
                    Logger.inst().info(f"Input muted: {obs_input['inputName']}={input_mute.input_muted}")

                    # Get input volume
                    input_volume = self.obs_connector.get_input_volume(name=obs_input['inputName'])
                    Logger.inst().info(f"Input volume db: {obs_input['inputName']}={input_volume.input_volume_db}")
                    Logger.inst().info(f"Input volume mul: {obs_input['inputName']}={input_volume.input_volume_mul}")
                # end if
            # end if
        # end for
    # end _show_debug_info

    # Connect to OBS
    def _connect_obs(self):
        """
        Connect to OBS
        """
        if not self.obs_connected:
            # Connect to OBS
            try:
                # Logger.inst().debug(f"get_stats: {self.obs_connector.get_stats()}")
                Logger.inst().info("Connecting to OBS...")
                self.obs_connector.connect()
                Logger.inst().info("Connected to OBS successfully!")
                self.obs_connected = True
                Logger.inst().debug(f"get_stats: {dir(self.obs_connector.get_stats())}")
                # Show debug info
                self._show_debug_info()

                # Register events
                self._register_events()

                # Dispatch init
                self.dispatch(source=self, data={'event': 'on_obs_connected', 'data': None})
            except Exception as e:
                self.last_connection_attempt = datetime.now()
                Logger.inst().error(f"Failed to connect to OBS: {e}")
                self.obs_connected = False
            # end try
        # end if
    # end _connect_obs

    def _register_events(self):
        """
        Register OBS events
        """
        # Log
        Logger.inst().info(f"Registered OBS events: {self.obs_connector.event_list}")

        # Register events
        self.obs_connector.register_event(OBSEvent.SCENE_CREATED, self._on_scene_created)
        self.obs_connector.register_event(OBSEvent.SCENE_REMOVED, self._on_scene_removed)
        self.obs_connector.register_event(OBSEvent.SCENE_NAME_CHANGED, self._on_scene_name_changed)
        self.obs_connector.register_event(OBSEvent.SCENE_LIST_CHANGED, self._on_scene_list_changed)
        self.obs_connector.register_event(OBSEvent.CURRENT_PROGRAM_SCENE_CHANGED, self._on_current_program_scene_changed)
        self.obs_connector.register_event(OBSEvent.CURRENT_PREVIEW_SCENE_CHANGED, self._on_current_preview_scene_changed)
        self.obs_connector.register_event(OBSEvent.STREAM_STATE_CHANGED, self._on_stream_state_changed)
        self.obs_connector.register_event(OBSEvent.RECORD_STATE_CHANGED, self._on_record_state_changed)
        self.obs_connector.register_event(OBSEvent.INPUT_ACTIVE_STATE_CHANGED, self._on_input_active_state_changed)
        self.obs_connector.register_event(OBSEvent.INPUT_SHOW_STATE_CHANGED, self._on_input_show_state_changed)
        self.obs_connector.register_event(OBSEvent.INPUT_MUTE_STATE_CHANGED, self._on_input_mute_state_changed)
    # end _register_events

    # endregion PRIVATE

    # region EVENTS

    # On periodic tick
    def on_periodic_tick(self, time_i: int, time_count: int):
        """
        Event handler for the "periodic" event.

        :param time_i: Current time index.
        :type time_i: int
        :param time_count: Total time count.
        :type time_count: int
        """
        # Super call
        super().on_periodic_tick(time_i, time_count)

        # Reconnect to OBS if not connected, check connection
        if datetime.now() - self.last_connection_attempt > timedelta(seconds=5):
            if not self.obs_connected:
                Logger.inst().info("Reconnecting to OBS...")
                self._connect_obs()
            else:
                # Check connection
                try:
                    self.obs_connector.get_stats()
                except (
                        ws_exceptions.WebSocketConnectionClosedException,
                        json.decoder.JSONDecodeError,
                        obs_error.OBSSDKRequestError
                ) as e:
                    Logger.inst().error(f"OBS connection closed: {e}")
                    self.obs_connected = False
                    self.dispatch(source=self, data={'event': 'on_obs_disconnected'})
                # end if
            # end if
        # end if
    # end on_periodic_tick

    # On scene created event handler
    def _on_scene_created(self, data):
        """
        On scene created event handler.

        :param data: The event data.
        :type data: Any
        """
        # Log
        Logger.inst().event(self.__class__.__name__, self.name, "on_scene_created", data=data)
        self.dispatch(source=self, data={'event': 'on_scene_created', 'data':data})
    # end on_scene_created

    # On scene removed event handler
    def _on_scene_removed(self, data):
        """
        On scene removed event handler.

        :param data: The event data.
        :type data: Any
        """
        # Log
        Logger.inst().event(self.__class__.__name__, self.name, "on_scene_removed", data=data)
        self.dispatch(source=self, data={'event': 'on_scene_removed', 'data':data})
    # end on_scene_removed

    # On scene name changed event handler
    def _on_scene_name_changed(self, data):
        """
        On scene name changed event handler.

        :param data: The event data.
        :type data: Any
        """
        # Log
        Logger.inst().event(self.__class__.__name__, self.name, "on_scene_name_changed", data=data)
        self.dispatch(source=self, data={'event': 'on_scene_name_changed', 'data':data})
    # end on_scene_name_changed

    # On scene list changed event handler
    def _on_scene_list_changed(self, data):
        """
        On scene list changed event handler.

        :param data: The event data.
        :type data: Any
        """
        # Log
        Logger.inst().event(self.__class__.__name__, self.name, "on_scene_list_changed", data=data)
        self.dispatch(source=self, data={'event': 'on_scene_list_changed', 'data':data})
    # end on_scene_list_changed

    # On current program scene changed event handler
    def _on_current_program_scene_changed(self, data):
        """
        On current program scene changed event handler.

        :param data: The event data.
        :type data: Any
        """
        # Log
        Logger.inst().event(self.__class__.__name__, self.name, "on_current_program_scene_changed", data=data)
        self.dispatch(source=self, data={'event': 'on_current_program_scene_changed', 'data':data})
    # end on_current_program_scene_changed

    # On current preview scene changed event handler
    def _on_current_preview_scene_changed(self, data):
        """
        On current preview scene changed event handler.

        :param data: The event data.
        :type data: Any
        """
        # Log
        Logger.inst().event(self.__class__.__name__, self.name, "on_current_preview_scene_changed", data=data)
        self.dispatch(source=self, data={'event': 'on_current_preview_scene_changed', 'data':data})
    # end on_current_preview_scene_changed

    # On stream state changed event handler
    def _on_stream_state_changed(self, data):
        """
        On stream state changed event handler.

        :param data: The event data.
        :type data: Any
        """
        # Log
        Logger.inst().event(self.__class__.__name__, self.name, "on_stream_state_changed", data=data)
        self.dispatch(source=self, data={'event': 'on_stream_state_changed', 'data':data})
    # end on_stream_state_changed

    # On record state changed event handler
    def _on_record_state_changed(self, data):
        """
        On record state changed event handler.

        :param data: The event data.
        :type data: Any
        """
        # Log
        Logger.inst().event(self.__class__.__name__, self.name, "on_record_state_changed", data=data)
        self.dispatch(source=self, data={'event': 'on_record_state_changed', 'data':data})
    # end on_record_state_changed

    # On input active state changed event handler
    def _on_input_active_state_changed(self, data):
        """
        On input active state changed event handler.

        :param data: The event data.
        :type data: Any
        """
        # Log
        Logger.inst().event(self.__class__.__name__, self.name, "on_input_active_state_changed", data=data)
        self.dispatch(source=self, data={'event': 'on_input_active_state_changed', 'data':data})
    # end on_input_active_state_changed

    # On input show state changed event handler
    def _on_input_show_state_changed(self, data):
        """
        On input show state changed event handler.

        :param data: The event data.
        :type data: Any
        """
        # Log
        Logger.inst().event(self.__class__.__name__, self.name, "on_input_show_state_changed", data=data)
        self.dispatch(source=self, data={'event': 'on_input_show_state_changed', 'data': data})
    # end on_input_show_state_changed

    # On input mute state changed event handler
    def _on_input_mute_state_changed(self, data):
        """
        On input mute state changed event handler.

        :param data: The event data.
        :type data: Any
        """
        # Log
        Logger.inst().event(self.__class__.__name__, self.name, "on_input_mute_state_changed", data=data)
        self.dispatch(source=self, data={'event': 'on_input_mute_state_changed', 'data':data})
    # end on_input_mute_state_changed

    # endregion EVENTS

# end OBSPanel

