# Built-Ins
from typing import Generic, TypeVar

# Local Imports
from .base_controller import BaseController
from .image_controller import ImageController
from .measurement_controller import MeasurementController
from pycubeview.global_app_state import AppState
from pycubeview.ui.widgets.image_display import ImageDisplay
from pycubeview.ui.widgets.meas_display import MeasurementAxisDisplay

T = TypeVar("T", ImageDisplay, MeasurementAxisDisplay)
U = TypeVar("U", ImageController, MeasurementController)


class FollowController(BaseController, Generic[T, U]):
    def __init__(
        self,
        global_state: AppState,
        display_pair: tuple[T, T],
        display_pair_controllers: tuple[U, U],
    ) -> None:
        self.follower: T = display_pair[0]
        self.leader: T = display_pair[1]

        self.follower_ctrl: U = display_pair_controllers[0]
        self.leader_ctrl: U = display_pair_controllers[1]

        super().__init__(global_state)

    def _build_actions(self) -> None:
        return

    def _install_actions(self) -> None:
        return

    def _connect_signals(self) -> None:
        return


class ImageFollower(FollowController[ImageDisplay, ImageController]):
    def __init__(
        self,
        global_state: AppState,
        display_pair: tuple[ImageDisplay, ImageDisplay],
        display_pair_controllers: tuple[ImageController, ImageController],
    ) -> None:
        super().__init__(global_state, display_pair, display_pair_controllers)
        self._connect_signals()

    def _connect_signals(self) -> None:
        self.leader.pixel_clicked.connect(self.follower.pixel_clicked.emit)
        self.leader.pixel_double_clicked.connect(
            self.follower.pixel_double_clicked.emit
        )
        self.leader.point_plotted.connect(self.follower.point_plotted.emit)
        self.leader.point_deleted.connect(self.follower.point_deleted.emit)
        self.leader.data_tracking.connect(self.follower.data_tracking.emit)

    def plot_existing_points(self):
        for i in self.leader_ctrl.scatter_cache:
            self.leader._vbox.addItem(i)
        for j in self.leader_ctrl.poly_cache.values():
            self.leader._vbox.addItem(j)


class MeasurementFollower(
    FollowController[MeasurementAxisDisplay, MeasurementController]
):
    def __init__(
        self,
        global_state: AppState,
        display_pair: tuple[MeasurementAxisDisplay, MeasurementAxisDisplay],
        display_pair_controllers: tuple[
            MeasurementController, MeasurementController
        ],
    ) -> None:
        super().__init__(global_state, display_pair, display_pair_controllers)

    def _connect_signals(self) -> None:
        self.leader.measurement_added.connect(
            self.follower.measurement_added.emit
        )
        self.leader.measurement_deleted.connect(
            self.follower.measurement_deleted.emit
        )
        self.leader.measurement_changed.connect(
            self.follower.measurement_changed.emit
        )
