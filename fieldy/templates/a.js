function waitForTilesLoaded() {
  return new Promise(function(resolve) {
    var removeLoadListener = viewer.scene.globe.tileLoadProgressEvent.addEventListener(function(numberOfPendingTiles) {
      if (numberOfPendingTiles === 0) {
        removeLoadListener();
        resolve();
      }
    });
  });
}

function getClamping(pos) {
  let clampedPosition2;
  viewer.camera.flyTo({
    destination: pos,
    complete: async (e) => {
      await waitForTilesLoaded();
      clampedPosition2 = viewer.scene.clampToHeight(pos, [], 2);
    }
  });
}

// ---------------

let promiseChain = Promise.resolve();
const clampedPositions = [];

pathsData["이동4"].forEach((item, i) => {
    const cartesian = Cesium.Cartesian3.fromArray(item[0]);
    const cartographic = Cesium.Cartographic.fromCartesian(cartesian);
    cartographic.height = 100;
    const pos3 = Cesium.Cartesian3.fromRadians(cartographic.longitude, cartographic.latitude, cartographic.height)
    
    // 새로운 프라미스 체인 세그먼트 생성
    promiseChain = promiseChain.then(() => new Promise((resolve) => {
        viewer.camera.flyTo({
            destination: pos3,
            complete: () => {
                // 카메라 이동이 완료되면 타일 로딩을 기다립니다.
                // viewer.scene.globe.tileLoadProgressEvent.addEventListener(function onTileLoad(numberOfPendingTiles) {
                //     if (numberOfPendingTiles === 0) {
                //         viewer.scene.globe.tileLoadProgressEvent.removeEventListener(onTileLoad);

                        let clampedPosition = viewer.scene.clampToHeight(cartesian, [], 2);
                        // if (clampedPosition !== undefined) {
                            clampedPositions.push(clampedPosition);
                            resolve();
                //         }
                //     }
                // });
            }
        });
    }));
});

promiseChain.then(() => {
    console.log(clampedPositions);
});
