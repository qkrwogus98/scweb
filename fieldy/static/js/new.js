import * as Cesium from '/static/CesiumUnminified/Cesium.js';
import setTimeline from "./timeline.js";

// (async (Cesium) => {
// })(Cesium);

Cesium.Ion.defaultAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiIzMjM0YTQ5OS01MTgwLTRjODItYTk0MS04ODQ4ODE2YTdhNTEiLCJpZCI6MzI5MzEwLCJpYXQiOjE3NTQ0NzE0Mzd9.EuurwTHYuKDK-CHcjh1a22P4O6ijJNlb6f2qx8fZctA';

const viewer = new Cesium.Viewer('cesiumContainer', {
  // terrainProvider: await createWorldTerrainAsync()

  // must use the terrain option for clampToHeight
  terrain: Cesium.Terrain.fromWorldTerrain()
});
viewer.scene.globe.enableLighting = true;

setTimeline(viewer);

const dataSourcePromise = Cesium.CzmlDataSource.load(
  "/assets/GroundTest2.czml"
  // "http://sc.fieldylab.com/czml"
);

const entities = [];
const positionProperties = [];
viewer.dataSources.add(dataSourcePromise).then(function (dataSource) {
  dataSource.entities.values.forEach((item) => {
    if (!item.id.includes('Path')) {
      entities.push(item);
      positionProperties.push(item.position);

      // just for DumpTruck !!!
      // ADD
      const velocityOrientation = new Cesium.VelocityOrientationProperty(item.position);
      const correctedOrientation = new Cesium.CallbackProperty((time, result) => {
        const orientation = velocityOrientation.getValue(time, result);
        if (!Cesium.defined(orientation)) {
          return null;
        }

        const additionalRotation = Cesium.Transforms.headingPitchRollQuaternion(
          Cesium.Cartesian3.ZERO,
          new Cesium.HeadingPitchRoll(-Math.PI / 2 + Math.PI / 360 * 18, 0, 0)
        );
        return Cesium.Quaternion.multiply(orientation, additionalRotation, result);
      }, false);
      item.orientation = correctedOrientation;
    }
  });
  // entities[0].model.color = Cesium.Color.fromRandom({alpha: 1.0});
  // entities[0].model.colorBlendMode = Cesium.ColorBlendMode.MIX;
  // entities[0].model.colorBlendAmount = 0.5;

  console.log(entities)
});

function start() {
  viewer.clock.shouldAnimate = true;
  viewer.scene.postRender.addEventListener(() => {
    const zOffset = 5;  // z+ offset for CAT_785C.glb model

    entities.forEach((entity, i) => {
      try {
        const position = positionProperties[i].getValue(viewer.clock.currentTime);
        // TODO: czml 만들때 시간 position 부분 꽉 채우기
        const clampedPosition = viewer.scene.clampToHeight(position, entities);
        if (!Cesium.defined(clampedPosition))
          return
        const cartographicPosition = Cesium.Cartographic.fromCartesian(clampedPosition);
        cartographicPosition.height += zOffset;
        const adjustedPosition = Cesium.Cartesian3.fromRadians(cartographicPosition.longitude, cartographicPosition.latitude, cartographicPosition.height);
        entity.position = adjustedPosition;
      } catch (e) {
        // console.log(e, viewer.clock.currentTime);
      }
    });
  });
}

const ahdmrl = [];

// Add click event handler
const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
handler.setInputAction((event) => {
  var ellipsoid = viewer.scene.globe.ellipsoid;
  var cartesian = viewer.camera.pickEllipsoid(event.position, ellipsoid);

  if (cartesian) {
    console.log(cartesian)
    var cartographic = ellipsoid.cartesianToCartographic(cartesian);
    var lon = Cesium.Math.toDegrees(cartographic.longitude);
    var lat = Cesium.Math.toDegrees(cartographic.latitude);

    // console.log('Clicked Location:', {latitude: lat, longitude: lon});

    viewer.entities.add({
      position: cartesian,
      point: {
        pixelSize: 10,
        color: Cesium.Color.RED
      }
    })
  } else {
    console.log('Clicked outside the globe.');
  }

  var pickedLocation = viewer.scene.pickPosition(event.position);

  if (Cesium.defined(pickedLocation)) {
    console.log(pickedLocation.x, pickedLocation.y, pickedLocation.z)
    var cartographic = Cesium.Ellipsoid.WGS84.cartesianToCartographic(cartesian);
    var longitude = Cesium.Math.toDegrees(cartographic.longitude);
    var latitude = Cesium.Math.toDegrees(cartographic.latitude);
    var height = cartographic.height;
    console.log(lon, lat, height);
    ahdmrl.push([[pickedLocation.x, pickedLocation.y, pickedLocation.z], [longitude, latitude]])
    viewer.entities.add({
      position: pickedLocation,
      point: {
        pixelSize: 10,
        color: Cesium.Color.RED
      }
    });
  }


}, Cesium.ScreenSpaceEventType.LEFT_CLICK);

handler.setInputAction((event) => {
  console.log(ahdmrl);
}, Cesium.ScreenSpaceEventType.RIGHT_CLICK);



var position = Cesium.Cartesian3.fromDegrees(127.22094296282091, 150);
console.log(position)
position = viewer.scene.clampToHeight(position, entities)
position = new Cesium.Cartesian3(-3082383.2212016094, 4057811.858921894, 3823193.6214806363)
var heading = Cesium.Math.toRadians(96);
var pitch = 0;
var roll = 0;
// var orientation2 = Cesium.Transforms.headingPitchRollQuaternion(position, new Cesium.HeadingPitchRoll(heading, pitch, roll));
console.log(position)
const entity3 = viewer.entities.add({
  name: 'gltf Model',
  position: position,
  // orientation: orientation2,
  point: {
    pixelSize: 10,
    color:Cesium.Color.BLUE
  }
  // model: {
  //   uri: '/assets/CAT_785C.glb',
  //   scale: 0.2
  // }
});
viewer.trackedEntity = entities[2]


const tileset = await Cesium.Cesium3DTileset.fromUrl(
  '/assets/hanwha1/tileset.json'
);
// tileset.style = new Cesium.Cesium3DTileStyle({
//   pointSize: 2.5
// });
viewer.scene.primitives.add(tileset);

const bs = tileset.boundingSphere;

var cartographic = Cesium.Cartographic.fromCartesian(bs.center);
var lon = Cesium.Math.toDegrees(cartographic.longitude);
var lat = Cesium.Math.toDegrees(cartographic.latitude);

// Move the camera from the center of the tileset to a point that is 2.5 times the radius of the boundingSphere
const heightAboveTileset = cartographic.height + (bs.radius * 2.5);
const destination = Cesium.Cartesian3.fromDegrees(lon, lat, heightAboveTileset);
// const destination = new Cesium.Cartesian3(
//   -3082221.658267818, 4058170.7095429287, 3823446.750647112
// );
const orientation = new Cesium.HeadingPitchRoll(
  // 1.727787686466434, -0.7302563148704717, 0.000059123963379370537
  1.727787686466434, -Cesium.Math.PI_OVER_TWO, 0.000059123963379370537
);

console.log(ENV_MODE)

if (ENV_MODE === 'production') {
  viewer.camera.flyTo({
    destination: destination /* bs.center */, orientation: orientation,
    complete: () => {
      start();
    }
  });
} else {
  viewer.camera.setView({
    destination: destination, orientation: orientation,
    endTransform: Cesium.Matrix4.IDENTITY,
  });
  start();
}
