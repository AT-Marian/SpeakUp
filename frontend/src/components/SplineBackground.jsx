import React, { Suspense, useState, useEffect } from 'react';
import Spline from '@splinetool/react-spline';

export default function SplineBackground() {
  const sceneId = 'https://prod.spline.design/vBk-ipO-rWajDaRs/scene.splinecode';

  return (
    <div className="w-full h-full relative"> 
      <Suspense fallback={<div>Loading 3D...</div>}>
        {/* We make the Spline component fill the container 
            and ensure it's on top of the gradient background.
        */}
        <div className="w-full h-full">
          <Spline scene={sceneId} />
        </div>
      </Suspense>
    </div>
  );
}