import * as Cesium from "cesium";
import { DateTime } from "/static/luxon.min.js";

export default function setTimeline(viewer) {
  const datetimeFormatter = (date, formatter) => {
    const jsDate = Cesium.JulianDate.toDate(date);
    const dateTime = DateTime.fromJSDate(jsDate).setZone("local");
    return dateTime.toLocaleString(formatter);
  };

  viewer.animation.viewModel.timeFormatter = (date, viewModel) =>
    datetimeFormatter(date, DateTime.TIME_WITH_SECONDS);

  viewer.animation.viewModel.dateFormatter = (date, viewModel) =>
    datetimeFormatter(date, DateTime.DATE_SHORT);

  viewer.timeline.makeLabel = (date) =>
    datetimeFormatter(date, DateTime.DATETIME_SHORT_WITH_SECONDS);
}
