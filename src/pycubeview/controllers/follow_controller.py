# Built-Ins
from typing import Generic, TypeVar

# Local Imports
from .base_controller import BaseController
from .image_controller import ImageController
from .measurement_controller import MeasurementController
from pycubeview.global_app_state import AppState
from pycubeview.ui.widgets.image_display import ImageDisplay
from pycubeview.ui.widgets.meas_display import MeasurementAxisDisplay
from pycubeview.data_transfer_classes import (
    ImageScatterPoint,
    ImagePolygon,
    Measurement,
)

# PySide6 Imports
from PySide6.QtWidgets import QGraphicsPolygonItem
from PySide6.QtCore import Slot

T = TypeVar("T", ImageDisplay, MeasurementAxisDisplay)
U = TypeVar("U", ImageController, MeasurementController)


class FollowController(BaseController, Generic[T, U]):
    def __init__(
        self,
        global_state: AppState,
        display_pair: tuple[T, T],
        display_pair_controllers: tuple[U, U],
    ) -> None:
        print("INITIALIZING BASE FOLLOWER")
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
        print("INTIALIZING IMAGE FOLLOWER")
        self.plot_existing_points()
        self.plot_existing_polygons()

    def _connect_signals(self) -> None:
        print("Connecting Follower Signals...")
        self.follower.pixel_clicked.connect(self.leader.pixel_clicked.emit)
        self.follower.pixel_double_clicked.connect(
            self.leader.pixel_double_clicked.emit
        )
        self.follower.point_plotted.connect(self.leader.point_plotted.emit)
        self.follower.point_deleted.connect(self.leader.point_deleted.emit)
        self.follower.data_tracking.connect(self.leader.data_tracking.emit)
        self.follower_ctrl._lasso.lasso_finished.connect(
            self.leader_ctrl._lasso.lasso_finished
        )
        self.leader_ctrl.scatter_added.connect(self.plot_new_point)
        self.leader_ctrl.scatter_removed.connect(
            self.follower_ctrl.remove_point_from_cache
        )
        self.leader_ctrl.poly_added.connect(self.plot_new_poly)
        self.leader_ctrl.poly_removed.connect(
            self.follower_ctrl.remove_poly_from_cache
        )

    def plot_existing_points(self):
        for i in self.leader_ctrl.scatter_cache:
            self.plot_new_point(i)

    def plot_existing_polygons(self):
        for poly in self.leader_ctrl.poly_cache:
            qpoly = QGraphicsPolygonItem(poly.polygon_item.polygon())
            qpoly.setPen(poly.polygon_item.pen())
            new_poly = ImagePolygon(id=poly.id, polygon_item=qpoly)
            self.follower_ctrl.poly_cache.append(new_poly)
            self.follower_ctrl.add_polygon_by_id(new_poly.id)

    @Slot(ImageScatterPoint)
    def plot_new_point(self, scatter_point: ImageScatterPoint):
        new_scatter_pt = self.follower.plot_point(
            y=scatter_point.y,
            x=scatter_point.x,
            color=scatter_point.color,
            identifier=scatter_point.id,
            silent=True,
        )
        self.follower_ctrl.add_point_to_cache(new_scatter_pt)

    @Slot(ImagePolygon)
    def plot_new_poly(self, polygon: ImagePolygon):
        new_qpoly = QGraphicsPolygonItem(polygon.polygon_item.polygon())
        new_qpoly.setPen(polygon.polygon_item.pen())
        new_img_poly = ImagePolygon(id=polygon.id, polygon_item=new_qpoly)
        self.follower_ctrl.poly_cache.append(new_img_poly)
        self.follower_ctrl.add_polygon_by_id(new_img_poly.id)


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
        self.leader_ctrl.added_to_cache.connect(self.transfer_measurement)

    @Slot(Measurement)
    def transfer_measurement(self, measurement: Measurement):
        self.follower.add_measurement(
            x=measurement.pixel_x,
            y=measurement.pixel_y,
            x_pixels=measurement.x_pixels,
            y_pixels=measurement.y_pixels,
            id=measurement.id,
            silent=True,
        )
