# Local Imports
from pycubeview.global_app_state import AppState
from .file_controller import FileController
from .image_controller import ImageController
from .link_controller import LinkController
from .follow_controller import FollowController
from .measurement_controller import MeasurementController
from pycubeview.models.selection_model import SelectionModel
from pycubeview.data_transfer_classes import CursorTracker, LassoData
from pycubeview.ui.widgets.image_display import ImageDisplay
from pycubeview.ui.widgets.meas_display import MeasurementAxisDisplay
from pycubeview.ui.main_cubeview_window import CubeViewMainWindow


# PySide6 Imports
from PySide6.QtCore import QObject, Slot


class ROIMeasurementAdapter(QObject):
    def __init__(self, receiver: MeasurementController) -> None:
        super().__init__()
        self.receiver = receiver

    @Slot(LassoData)
    def handle(self, lasso_data: LassoData) -> None:
        xpixels = lasso_data.lasso_pixels[:, 0]
        ypixels = lasso_data.lasso_pixels[:, 1]
        self.receiver._meas.add_measurement(
            x_pixels=xpixels, y_pixels=ypixels, id=lasso_data.id
        )


class MainController(QObject):
    def __init__(self, window: CubeViewMainWindow) -> None:
        super().__init__()
        self._window = window
        self.app_state = AppState()
        self.file = FileController(self.app_state, window)
        self.image_controllers: list[ImageController] = []
        self.measurement_controllers: list[MeasurementController] = []
        self.link_controllers: list[LinkController] = []
        self.follow_controllers: list[FollowController] = []
        self._roi_adapters: list[ROIMeasurementAdapter] = []

        self.selection_model = SelectionModel()

        self._connect_signals()

    def _connect_signals(self):
        self._window.image_display_added.connect(self._on_adding_image_display)
        self._window.measurement_display_added.connect(
            self._on_adding_measurement_display
        )
        self._window.link_displays.connect(self._on_linking_displays)
        self._window.follow_img_display.connect(self._following_img_displays)
        self._window.follow_meas_display.connect(self._following_meas_displays)

    @Slot(ImageDisplay)
    def _on_adding_image_display(self, img_display: ImageDisplay):
        print("Image Display Controller Connected")
        img_display.data_tracking.connect(self._update_tracking_status)
        controller = ImageController(
            self.app_state, self.selection_model, img_display
        )
        self.image_controllers.append(controller)

        # Connecting Lasso Signal
        for i in self.measurement_controllers:
            adapter = ROIMeasurementAdapter(i)
            self._roi_adapters.append(adapter)
            controller.lasso_plotted.connect(adapter.handle)

    @Slot(MeasurementAxisDisplay)
    def _on_adding_measurement_display(
        self, meas_display: MeasurementAxisDisplay
    ):
        meas_display.max_plotted.connect(self._update_max_warning)
        controller = MeasurementController(
            self.app_state, self.selection_model, meas_display
        )
        self.measurement_controllers.append(controller)

        # Connecting Lasso Signal
        for i in self.image_controllers:
            adapter = ROIMeasurementAdapter(controller)
            self._roi_adapters.append(adapter)
            i.lasso_plotted.connect(adapter.handle)

    @Slot(ImageDisplay, MeasurementAxisDisplay)
    def _on_linking_displays(
        self,
        img_display: ImageDisplay,
        meas_display: MeasurementAxisDisplay,
    ):
        print("Displays Linked")
        link_controller = LinkController(
            self.app_state, img_display, meas_display
        )
        self.link_controllers.append(link_controller)

    @Slot(ImageDisplay, ImageDisplay)
    def _following_img_displays(
        self,
        follower: ImageDisplay,
        leader: ImageDisplay,
    ) -> None:
        follower_controller: ImageController | None = None
        leader_controller: ImageController | None = None
        print(f"Searching for: {follower.id}")
        for i in self.image_controllers:
            print(f"   testing: {i._img_disp.id}")
            if i._img_disp.id == follower.id:
                follower_controller = i
            if i._img_disp.id == leader.id:
                leader_controller = i
        if (follower_controller is None) or (leader_controller is None):
            raise ValueError("Controllers not found in image follower setup.")
        follow_controller = FollowController(
            self.app_state,
            (follower, leader),
            (follower_controller, leader_controller),
        )
        self.follow_controllers.append(follow_controller)

    @Slot(MeasurementAxisDisplay, MeasurementAxisDisplay)
    def _following_meas_displays(
        self,
        follower: MeasurementAxisDisplay,
        leader: MeasurementAxisDisplay,
    ) -> None:
        follower_controller: MeasurementController | None = None
        leader_controller: MeasurementController | None = None
        for i in self.measurement_controllers:
            if i._meas == follower:
                follower_controller = i
            if i._meas == leader:
                leader_controller = i
        if (follower_controller is None) or (leader_controller is None):
            raise ValueError("Controllers not found in image follower setup.")
        follow_controller = FollowController(
            self.app_state,
            (follower, leader),
            (follower_controller, leader_controller),
        )
        self.follow_controllers.append(follow_controller)

    @Slot(CursorTracker)
    def _update_tracking_status(self, cursor_tracker: CursorTracker):
        pval = cursor_tracker.value
        if pval.pixel_type == "single":
            self._window.status_bar.showMessage(
                f"x: {cursor_tracker.x_exact:.2f}, "
                f"y: {cursor_tracker.y_exact:.2f}, "
                f"value: {pval.v:.4f}"
            )
        elif pval.pixel_type == "rgb":
            self._window.status_bar.showMessage(
                f"x: {cursor_tracker.x_exact:.2f}, "
                f"y: {cursor_tracker.y_exact:.2f}, "
                f"r: {pval.r:.4f}, "
                f"g: {pval.g:.4f}, "
                f"b: {pval.b:.4f}"
            )

    @Slot()
    def _update_max_warning(self):
        self._window.status_bar.showMessage(
            "Maximum Number of Collected Spectra Reached. Save and Reset to"
            "continue collecting."
        )
