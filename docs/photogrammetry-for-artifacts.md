# **High-Fidelity Photogrammetry Pipeline for Small-Scale Archaeological Artifacts: An Integrated Python and C++ Engine Reference**

The digitization of archaeological artifacts measuring under 20 cm requires sub-millimeter geometric accuracy and high-fidelity, photorealistic textures. Traditional photography projects a 3D scene onto a 2D plane, losing depth information.2 To reverse this process, photogrammetry utilizes Structure-from-Motion (SfM) to resolve sparse geometry and camera poses, and Multi-View Stereo (MVS) to compute dense point clouds, surface meshes, and textures.2  
When utilizing a 4K action camera, developers face significant optical challenges.5 These compact devices employ ultra-wide-angle lenses that introduce extreme radial distortion and suffer from narrow depth-of-field constraints when capturing small objects at close range.5 This reference manual details the physical acquisition setups, mathematical camera calibration, software architectures, and advanced texture-mapping configurations necessary to maximize texture resolution using a Python-based pipeline.

## **Geometric Distortions and Rigorous Calibration of 4K Action Camera Sensors**

Action cameras are equipped with wide-angle or fisheye lenses to maximize the spatial field-of-view (FOV), typically ranging from ![][image1] to ![][image2].5 Consequently, their projections deviate heavily from the standard central pinhole camera model.5 Standard camera calibration algorithms rely on the Brown-Conrady model, which uses a polynomial expansion of radial and tangential distortion.5 This model projects a 3D world point ![][image3] onto the image plane by modeling radial distortion as:  
![][image4]  
![][image5]  
where ![][image6].8 This polynomial model fails to converge and becomes mathematically unstable when modeling the extreme barrel distortion of fisheye lenses, where light rays enter at angles exceeding ![][image7].8 To resolve this, a specialized projection model must be used.8 The Kannala-Brandt (equidistant) model is the standard for wide-angle fisheye lenses.10 This model projects a 3D world point using the entry angle ![][image8] of the incoming light ray relative to the optical axis 10:  
![][image9]  
The radial distortion function ![][image10] is represented as an odd-power polynomial expansion 10:  
![][image11]  
The distorted pixel coordinates ![][image12] on the sensor plane are computed as:  
![][image13]  
where ![][image14] represent the focal lengths in pixel units, and ![][image15] denote the coordinates of the principal point (optical center).8  
In Python, this calibration is performed using the cv2.fisheye module.8 A key implementation detail is that the 3D object points (objp) must have a shape of (N, 1, 3\) (where ![][image16] is the number of corners), unlike standard calibration which accepts (N, 3).8 Additionally, the standard cv2.calibrateCamera function must not be used on heavily distorted images, as it will fail to model the barrel distortion, leading to projection errors.8  
A crucial factor when calibrating 4K action cameras is that the active area of the sensor changes depending on the capture mode (e.g., still image vs. video) and aspect ratio (e.g., 4:3 vs. 16:9).5 For example, a 12 MP still photo uses a different portion of the sensor than a 4K video frame, altering the effective focal length and principal point.5 Consequently, separate self-calibration procedures must be applied for each individual recording resolution and mode used.5

| Geometric Parameter / Feature | Standard Pinhole (Brown-Conrady) | Kannala-Brandt (OpenCV Fisheye) | Scaramuzza Omnidirectional |
| :---- | :---- | :---- | :---- |
| **Maximum Field of View** | Up to ![][image17] 9 | Up to ![][image18] \- ![][image2] 9 | Up to ![][image19] 9 |
| **Radial Distortion Coefficients** | **![][image20]** 5 | ![][image21] 8 | Polynomial coefficients ![][image22] 10 |
| **Tangential Distortion** | Modeled via ![][image23] 8 | Omitted (assumed negligible) 8 | Modeled within projection plane alignment 9 |
| **Numerical Stability** | Diverges at ultra-wide angles 8 | Stable across extreme angles 8 | Exceptionally stable beyond ![][image2] 9 |
| **OpenCV Implementation** | cv2.calibrateCamera() 8 | cv2.fisheye.calibrate() 8 | Custom implementation / toolbox wrappers 9 |

During calibration, the execution of the estimation algorithm can fail even when corner detection is successful.11 This occurs during model computation due to numerical instability in the covariance matrix estimation.11 Setting the cv2.fisheye.CALIB\_CHECK\_COND flag causes the calibration solver to verify the conditioning of the projection matrices, throwing an exception if the dataset is geometrically degenerate.11

## **Micro-Scale Physical Acquisition Setup and Turntable Hardware Interface**

To capture maximum texture resolution for small-scale artifacts (under 20 cm), the physical environment must be designed to mitigate depth-of-field constraints and specular highlights.6

### **Depth of Field Management**

In close-up photogrammetry, the depth-of-field (DoF)—the region that remains in sharp focus—becomes thin.6 For a camera focusing on an object at close range, the total depth of field ![][image24] is approximated by:  
![][image25]  
where ![][image16] is the lens f-number (aperture), ![][image26] is the sensor's circle of confusion, ![][image27] is the distance to the subject, and ![][image28] is the focal length. Because action cameras typically feature small sensors and short focal lengths, they inherently possess wider DoFs than DSLRs at comparable distances.7 However, action camera apertures are fixed at wide settings (e.g., ![][image29] to ![][image30]).7  
To prevent out-of-focus areas, the subject distance ![][image27] must be optimized to balance resolution with depth of field.1 A 4K resolution setting (such as ![][image31] pixels for still images) yields a high pixel-to-millimeter ratio.1 Placing the camera ![][image32] from a ![][image33] object ensures the object fills the frame while maintaining a depth of field that keeps the entire object in sharp focus.1

### **Turntable Hardware Interface**

A motorized turntable is used to rotate the artifact while the camera remains on a stable tripod.1 An Arduino Nano microcontroller connected via USB serial or Bluetooth controls a 5V stepper motor via a ULN2003A Darlington transistor array.7 The microcontroller's firmware rotates the turntable platter in increments of ![][image34], triggering the camera shutter at each step to capture 36 images per rotation.7

* **Background Masking**: The turntable is covered with a matte, monochrome black or white cloth.7 This enables automatic background masking in Python, which prevents the stationary background from corrupting the SfM camera pose computation.7  
* **Camera Orbits**: Image capture must be executed in a multi-orbit pattern to ensure complete coverage. For a ![][image33] object, three elevation angles are used: low (![][image35]), medium (![][image36]), and high (![][image37]).1 At each elevation, the turntable is rotated in increments of ![][image34], yielding 36 images per orbit (108 images total).1  
* **Articulated Merging**: To reconstruct the base of the artifact, the object must be flipped upside down, and a second set of orbits must be captured.12 Feature matching links the two distinct orientations, and bundle adjustment aligns them into a single, water-tight 3D coordinate space.7 A scale bar of exact dimensions must be placed in the scene to resolve the absolute metric scale of the reconstruction.7

| Acquisition Variable | Computer-Controlled DSLR Setup | Smartphone Bluetooth Setup | 4K Action Camera Python Pipeline |
| :---- | :---- | :---- | :---- |
| **Typical Sensor Size** | APS-C or Full Frame | ![][image38]\-inch class 7 | ![][image39]\-inch class 5 |
| **Focal Length (![][image28])** | **![][image40]** Macro 7 | ![][image41] \- ![][image42] 7 | ![][image43] \- ![][image44] (Ultra-wide) 5 |
| **Aperture (![][image16])** | **![][image45]** (stopped down) 7 | ![][image29] (fixed) 7 | ![][image30] (fixed) 7 |
| **Subject Distance (![][image27])** | **![][image46]** 7 | ![][image47] 7 | ![][image47] |
| **Resulting DoF Boundary** | **![][image48]** (highly sharp) 7 | ![][image49] (geometric degradation) 7 | ![][image50] (highly sharp due to short ![][image28]) 7 |
| **Spatial Resolution** | **![][image51]** (![][image31]) 5 | ![][image52] (![][image53]) 7 | ![][image54] (![][image31]) 5 |
| **Scale Resolution** | Automated via 130mm plate 7 | Automated via 130mm plate 7 | Manual scale bar integration 12 |

### **Cross-Polarization**

To eliminate specular highlights (reflections), a cross-polarization setup must be implemented.1 Specular highlights shift across the surface of the artifact as the camera or object moves, which confuses feature matching algorithms and produces severe artifacts in the final mesh.1  
Linear polarizing sheets are placed over the light sources, and a circular polarizing filter is attached to the action camera's lens.1 Adjusting the polarizer until specular highlights disappear allows the sensor to capture diffuse albedo textures. A continuous ring light or a diffuse overhead LED panel positioned approximately ![][image55] directly above the center of the turntable provides homogeneous lighting that prevents rotational lighting variations as the object spins.6

## **Pipeline Software Architecture and Framework Options**

A Python-based photogrammetry pipeline can be constructed using either a pure Python framework (OpenSfM) or a hybrid system that wraps high-performance C++ engines (OpenMVG \+ OpenMVS).15

### **Pure Python Architecture (OpenSfM)**

OpenSfM is written primarily in Python and utilizes OpenCV and Ceres Solver for reconstruction.18 It natively supports the standard OpenCV fisheye model and handles camera model overrides.4 The standard OpenSfM pipeline executes the following sequence:

1. **extract\_metadata**: Parses EXIF data to extract focal length and image dimensions, writing a camera\_models.json file.4  
2. **detect\_features**: Computes scale-invariant keypoints (SIFT or HAAR).2  
3. **match\_features**: Matches keypoints across image pairs.4  
4. **create\_tracks**: Links pairwise matches into multi-view tracks, saving the output in tracks.csv.4  
5. **reconstruct**: Solves the incremental SfM problem, outputting camera poses and a sparse point cloud in reconstruction.json.4  
6. **undistort**: Generates radially undistorted images and camera models.4  
7. **compute\_depthmaps**: Performs dense stereo matching to output depth maps and a dense point cloud (merged.ply).4

OpenSfM's configuration is managed through a config.yaml file, and camera model overrides can be specified globally or per-camera using a camera\_models\_overrides.json file in the dataset's root folder.4 For example, setting the camera ID to "all" forces all cameras in the dataset to use a specific projection model 4:

JSON  
{  
    "all": {  
        "projection\_type": "fisheye\_opencv",  
        "width": 4000,  
        "height": 3000,  
        "focal": 0.58,  
        "k1": \-0.012,  
        "k2": 0.003,  
        "k3": \-0.001,  
        "k4": 0.0  
    }  
}

This configuration ensures that OpenSfM bypasses its default perspective projection assumptions and initializes the reconstruction with the correct fisheye distortion parameters.4

### **Hybrid C++ Wrapper Architecture (OpenMVG \+ OpenMVS)**

To achieve maximum geometric accuracy and texture quality, a hybrid system that executes compiled C++ binaries via Python’s subprocess module is preferred.21 OpenMVG excels at precise camera localization and sparse reconstruction.4 OpenMVS is the industry-standard engine for dense point cloud computation, mesh reconstruction, and high-fidelity texturing.16

| Pipeline Stage | OpenSfM Native Node | Hybrid C++ Executable Counterpart | Crucial CLI Parameters & Flags |
| :---- | :---- | :---- | :---- |
| **Metadata Extraction** | bin/opensfm extract\_metadata | openMVG\_main\_SfMInit\_ImageListing | \-f (force focal in px), \-k (K-matrix) 27 |
| **Feature Extraction** | bin/opensfm detect\_features | openMVG\_main\_ComputeFeatures | \-m SIFT (high resolution SIFT descriptors) 21 |
| **Geometric Matching** | bin/opensfm match\_features | openMVG\_main\_ComputeMatches | \-r 0.8 (ratio test threshold to filter outliers) 27 |
| **Sparse SFM Reconstruction** | bin/opensfm reconstruct | openMVG\_main\_IncrementalSfM | Incremental loop with strict resection filters 21 |
| **Format Conversion** | Native JSON representation | openMVG\_main\_openMVG2openMVS | \-i sfm\_data.bin \-d output\_dir \-o scene.mvs 16 |
| **MVS Densification** | bin/opensfm compute\_depthmaps | DensifyPointCloud | \--resolution-level 1 (retains full 4K detail) 21 |
| **Mesh Generation** | bin/opensfm mesh | ReconstructMesh | Generates continuous manifold surface mesh 16 |
| **Mesh Refinement** | N/A | RefineMesh | \--resolution-level 1 (recovers fine details) 29 |
| **High-Res Texturing** | Basic UV mapping 4 | TextureMesh | \--local-seam-leveling 1 \--global-seam-leveling 1 30 |

## **Advanced High-Resolution Texturing and Parameter Optimization**

To generate a texture at the maximum possible resolution, the texturing pipeline must utilize advanced view-selection, seam-leveling, and UV-unwrapping algorithms.26

### **The Waechter et al. Texturing Algorithm**

Both OpenMVS and AliceVision implement variations of the Waechter et al. texturing algorithm.26 Rather than averaging pixel colors across all visible views—which results in blurring due to minor camera registration errors—the algorithm treats texturing as a labeling problem.31 Each triangle face in the reconstructed mesh is assigned a single "best" source image.31  
The optimal view is selected by maximizing a quality cost function 32:

1. **area**: Selects the image where the camera viewing ray is most aligned with the face normal, maximizing projected spatial resolution.33  
2. **center**: Selects the image where the face projects closest to the image center, minimizing lens distortion and chromatic aberration.33

### **Seam Leveling and Exposure Compensation**

Assigning different source images to adjacent faces produces sharp color boundaries (seams) due to minor variations in camera exposure or lighting.30 To resolve this, two post-processing steps are executed:

* **Global Seam Leveling**: Adjusts the global color and exposure of each source image to harmonize the dataset before projection.30  
* **Local Seam Leveling**: Computes a transition boundary along the edges between adjacent texture patches, utilizing Poisson image editing or multi-band frequency blending to blend the color transition seamlessly.26

A known bug in the OpenMVS texturing module causes the output texture to render completely black along patch borders or across the entire mesh when \--local-seam-leveling and \--global-seam-leveling are enabled alongside active mask labels.30 This is caused by numerical discrepancies in the rasterizer mask during projection.30 Disabling these seam leveling options resolves the black texture issue, but degrades the overall visual continuity of the mesh.30 To maintain texture quality, developers must ensure that the input masks are clean and configure the \--ignore-mask-label parameter to match the active mask identifier.30

| Feature or Setting | OpenMVS TextureMesh Parameters | AliceVision Texturing Counterparts | Target Performance & Optimal Value |
| :---- | :---- | :---- | :---- |
| **Output Format** | \--export-type (obj, ply, gltf) 23 | Texture File Type (jpg, png, tiff) 26 | png or tiff for lossless resolution 26 |
| **Texture Scaling** | \--resolution-level (integer downscale) 21 | Texture Downscale (1, 2, 4, 8\) 26 | Set to 1 to retain full 4K sensor detail 26 |
| **Atlas Dimensions** | N/A (Internal automatic packing) | Texture Side (1024 to 16384\) 26 | 8192 or 16384 for maximum resolution 26 |
| **Seam Leveling** | \--local-seam-leveling / \--global-seam-leveling | Correct Exposure / Multi Band Downscale | Enable both; verify mask labels to avoid black textures 30 |
| **Unwrap Method** | Boundary conformal parameterization | Unwrap Method (Basic, LSCM, ABF) 26 | ABF (under 300k faces) or LSCM (under 600k) 26 |
| **Padding** | \--patch-packing-heuristic 21 | Padding (0-100 pixels) 26 | Recommended size: 2 to 4 px to prevent bleeding 26 |
| **Color Space** | Native sRGB / Linear | Process Colorspace 34 | Matches input camera color profile 34 |

### **State-of-the-Art Occlusion Texturing (GOATex)**

Hollow or highly concave archaeological vessels often present occluded interior geometries that are difficult to texture using standard projection methods.36 Standard project-and-inpaint pipelines rely on simple heuristic pixel filling (such as Voronoi propagation or smooth extrapolation) to fill occluded areas, which often produces blurry, semantically implausible textures and visible seams along the inner boundaries.38  
To solve this, advanced pipelines implement the GOATex occlusion-aware texturing framework.36 This method utilizes multi-view ray casting to segment the mesh into ordered visibility layers (![][image56]) based on "hit levels".38 For a collection of viewpoints ![][image26] and rays ![][image57], the directional influence ![][image58] of a mesh face ![][image28] at intersection order ![][image59] is computed as 38:  
![][image60]  
where ![][image61] is the unit normal of the face, and ![][image62] is the direction of the ray.38 Connected faces are grouped into "superfaces" using a spatial clustering algorithm, and each superface is assigned a uniform hit level 38:  
![][image63]  
This yields an ordered partition of the mesh into distinct visibility layers, from the outermost surfaces (![][image64]) to the deepest, fully occluded interior regions (![][image65]).38  
During projection, a two-stage visibility control strategy is applied: the outer layers are textured first, followed by normal flipping and backface culling to expose and texture the deeper interior layers without distorting the global coordinate structure.37 The resulting textures are merged in UV space using a soft blending scheme that weights each texture's contribution based on view-dependent visibility confidence.36 This process generates a continuous, seamless texture across both the exterior and interior surfaces of the model.36

## **Post-Processing and Geometric Validation in Open3D**

Once the textured mesh is generated, it must be verified and cleaned using Open3D's geometric engine.39

### **Topological Verification**

To ensure the 3D model is suitable for scientific analysis or 3D printing, it must be validated against several topological constraints 39:

* **Edge Manifold**: A mesh is edge manifold if every edge is shared by exactly one or two triangles.39 Edges shared by three or more triangles are non-manifold and represent physical impossibilities.39  
* **Vertex Manifold**: A mesh is vertex manifold if the star of each vertex (the set of surrounding faces and edges) is edge-manifold and edge-connected.39  
* **Watertight Solid**: A mesh is watertight if it has no holes, is edge and vertex manifold, and contains no self-intersecting triangles.39

These topological assertions are verified in Open3D using native boolean checks, which identify non-manifold boundaries and visualize self-intersections to guide the cleaning process.39

| Open3D Verification / Cleaning Function | Input Argument / Data Type | Topological Asset Validated |
| :---- | :---- | :---- |
| mesh.is\_edge\_manifold(allow\_boundary\_edges=True) | bool 39 | Verifies if all edges are bounded by 1 or 2 triangles 39 |
| mesh.is\_vertex\_manifold() | None 39 | Verifies if connected faces share continuous edges 39 |
| mesh.is\_self\_intersecting() | None 39 | Identifies if any triangles intersect other faces 39 |
| mesh.is\_watertight() | None 39 | Returns true if the mesh is manifold and has no holes 39 |
| mesh.remove\_degenerate\_triangles() | None 41 | Deletes triangles with zero area or collinear vertices 41 |
| mesh.remove\_duplicated\_vertices() | None 41 | Merges coincident vertices within a tolerance threshold 41 |
| mesh.remove\_small\_connected\_components(min\_tri) | int (minimum faces) 40 | Removes isolated noise clusters and floating geometry 40 |

### **Poisson Surface Reconstruction**

To generate a smooth, continuous mesh from an unstructured point cloud, the Poisson surface reconstruction algorithm is used.42 This algorithm solves for an indicator function of the solid volume using the point cloud normals, fitting a watertight surface to the points.42  
The resolution of the reconstructed mesh is controlled by the depth parameter, which specifies the maximum depth of the octree used by the solver.42 An octree depth ![][image66] divides the bounding volume into a grid of up to ![][image67] cells.42  
For a 20 cm archaeological artifact, the octree depth must be configured to balance geometric detail with noise filtering 42:

* **Low Depth (![][image68])**: Solves on a coarse grid (![][image69] cells), producing smooth surfaces but losing fine details such as tool marks or surface incisions.42  
* **Optimal Depth (![][image70])**: Solves on a fine grid (![][image71] to ![][image72] cells), recovering sub-millimeter geometric details and sharp features.42  
* **High Depth (![][image73])**: Solves on an extremely dense grid, which can introduce high-frequency noise and reconstruction artifacts from minor point misalignments.42

The Poisson reconstruction function also returns a density value for each vertex.43 These values can be used to filter out low-density regions where the algorithm has extrapolated triangles in areas with sparse point coverage.43

## **Complete Pipeline Implementation**

The following Python module is a production-ready implementation of the complete calibration, undistortion, reconstruction, and post-processing pipeline. It utilizes OpenCV for camera calibration, orchestrates the OpenMVG and OpenMVS engines via subprocesses, and loads the final textured mesh into Open3D for geometric validation.

Python  
import os  
import sys  
import glob  
import subprocess  
import cv2  
import numpy as np  
import open3d as o3d

class ArchaeologicalPhotogrammetryPipeline:  
    def \_\_init\_\_(self, workspace\_dir, camera\_id="action\_cam\_4k"):  
        self.workspace \= os.path.abspath(workspace\_dir)  
        self.camera\_id \= camera\_id  
          
        \# Define internal pipeline paths  
        self.raw\_images\_dir \= os.path.join(self.workspace, "images\_raw")  
        self.calib\_images\_dir \= os.path.join(self.workspace, "calibration")  
        self.undistorted\_dir \= os.path.join(self.workspace, "images\_undistorted")  
        self.mvg\_out\_dir \= os.path.join(self.workspace, "openmvg\_output")  
        self.mvs\_out\_dir \= os.path.join(self.workspace, "openmvs\_output")  
          
        \# Ensure directories exist  
        for path in \[self.raw\_images\_dir, self.calib\_images\_dir,   
                     self.undistorted\_dir, self.mvg\_out\_dir, self.mvs\_out\_dir\]:  
            os.makedirs(path, exist\_ok=True)  
              
        \# Calibration matrix placeholders  
        self.K \= None  
        self.D \= None  
        self.resolution \= None

    def calibrate\_fisheye\_camera(self, checkerboard\_dim=(9, 6), square\_size\_meters=0.025):  
        """  
        Executes sub-pixel chessboard detection and solves the Kannala-Brandt (equidistant)  
        fisheye camera calibration model.  
        """  
        criteria \= (cv2.TERM\_CRITERIA\_EPS \+ cv2.TERM\_CRITERIA\_MAX\_ITER, 30, 1e-6)  
          
        \# CRITICAL: For cv2.fisheye, object points MUST be shaped (1, N, 3\) where N is the total corners  
        total\_corners \= checkerboard\_dim \* checkerboard\_dim  
        objp \= np.zeros((1, total\_corners, 3), np.float32)  
        objp\[0, :, :2\] \= np.mgrid\[0:checkerboard\_dim, 0:checkerboard\_dim\].T.reshape(-1, 2\)  
        objp \*= square\_size\_meters

        obj\_points \=  \# 3D points in real world space  
        img\_points \=  \# 2D points in image plane  
          
        images \= glob.glob(os.path.join(self.calib\_images\_dir, "\*.jpg"))  
        if not images:  
            raise FileNotFoundError("No calibration images found in the calibration folder.")

        for fname in images:  
            img \= cv2.imread(fname)  
            gray \= cv2.cvtColor(img, cv2.COLOR\_BGR2GRAY)  
            self.resolution \= gray.shape\[::-1\]  \# (Width, Height)

            \# Find checkerboard corners  
            ret, corners \= cv2.findChessboardCorners(  
                gray, checkerboard\_dim,   
                cv2.CALIB\_CB\_ADAPTIVE\_THRESH \+ cv2.CALIB\_CB\_FAST\_CHECK \+ cv2.CALIB\_CB\_FILTER\_QUADS  
            )  
              
            if ret:  
                obj\_points.append(objp)  
                \# Refine corners to sub-pixel accuracy  
                corners\_sub \= cv2.cornerSubPix(gray, corners, (11, 11), (-1, \-1), criteria)  
                img\_points.append(corners\_sub)

        \# Solve equidistant model parameter estimation  
        N\_OK \= len(obj\_points)  
        if N\_OK \< 10:  
            raise ValueError(f"Insufficient valid calibration frames ({N\_OK}/10). Capture more orientations.")

        self.K \= np.zeros((3, 3))  
        self.D \= np.zeros((4, 1))  
        rvecs \= \[np.zeros((1, 1, 3), dtype=np.float32) for \_ in range(N\_OK)\]  
        tvecs \= \[np.zeros((1, 1, 3), dtype=np.float32) for \_ in range(N\_OK)\]  
          
        calibration\_flags \= (  
            cv2.fisheye.CALIB\_RECOMPUTE\_EXTRINSIC \+   
            cv2.fisheye.CALIB\_CHECK\_COND \+   
            cv2.fisheye.CALIB\_FIX\_SKEW  
        )

        try:  
            rms, \_, \_, \_, \_ \= cv2.fisheye.calibrate(  
                obj\_points, img\_points, self.resolution,  
                self.K, self.D, rvecs, tvecs, calibration\_flags, criteria  
            )  
            print(f"Calibration completed. RMS Error: {rms:.4f} pixels")  
            np.savez(os.path.join(self.workspace, "calibration\_params.npz"), K=self.K, D=self.D, res=self.resolution)  
        except Exception as e:  
            print("Fisheye calibration failed during model estimation. Verify checkerboard clarity.")  
            raise e

    def batch\_undistort\_images(self):  
        """  
        Applies calibrated equidistant parameters to undistort the 4K raw images,  
        transforming the geometry to a standard central pinhole projection.  
        """  
        if self.K is None or self.D is None:  
            calib\_file \= os.path.join(self.workspace, "calibration\_params.npz")  
            if os.path.exists(calib\_file):  
                data \= np.load(calib\_file)  
                self.K \= data\["K"\]  
                self.D \= data  
                self.resolution \= tuple(data\["res"\])  
            else:  
                raise ValueError("Calibration parameters missing. Execute calibration step.")

        raw\_images \= glob.glob(os.path.join(self.raw\_images\_dir, "\*.jpg"))  
        if not raw\_images:  
            raise FileNotFoundError("No raw images found to undistort.")

        \# Compute rectification maps using standard pinhole camera projection limits  
        map1, map2 \= cv2.fisheye.initUndistortRectifyMap(  
            self.K, self.D, np.eye(3), self.K, self.resolution, cv2.CV\_16SC2  
        )

        for img\_path in raw\_images:  
            img \= cv2.imread(img\_path)  
            undistorted\_img \= cv2.remap(  
                img, map1, map2,   
                interpolation=cv2.INTER\_LANCZOS4,   
                borderMode=cv2.BORDER\_CONSTANT  
            )  
            base\_name \= os.path.basename(img\_path)  
            cv2.imwrite(  
                os.path.join(self.undistorted\_dir, base\_name),   
                undistorted\_img,   
                 
            )  
        print(f"Batch undistortion completed for {len(raw\_images)} frames.")

    def execute\_openmvg\_sfm(self):  
        """  
        Executes Structure-from-Motion using OpenMVG command line binaries via subprocess.  
        """  
        sfm\_data\_path \= os.path.join(self.mvg\_out\_dir, "sfm\_data.json")  
        focal\_pixels \= max(self.resolution) \* 1.2  \# Heuristic camera model initialization  
          
        \# Step 1: Initialize image listing  
        cmd\_init \=};0;{self.K};0;{self.K};{self.K};0;0;1"  
        \]  
        subprocess.run(cmd\_init, check=True)

        \# Step 2: Compute SIFT features  
        cmd\_features \=  
        subprocess.run(cmd\_features, check=True)

        \# Step 3: Compute Matches with relative ratio filtering  
        cmd\_matches \=  
        subprocess.run(cmd\_matches, check=True)

        \# Step 4: Incremental Reconstruction  
        cmd\_reconstruct \=  
        subprocess.run(cmd\_reconstruct, check=True)

    def execute\_openmvs\_reconstruction(self):  
        """  
        Imports SfM data, computes dense point cloud, reconstructs mesh,  
        and applies Waechter et al. high-resolution multi-view texturing.  
        """  
        mvg\_bin\_data \= os.path.join(self.mvg\_out\_dir, "sfm\_data.bin")  
        mvs\_scene \= os.path.join(self.mvs\_out\_dir, "scene.mvs")  
          
        \# Step 1: Export OpenMVG scene to OpenMVS format  
        cmd\_export \=  
        subprocess.run(cmd\_export, check=True)

        \# Step 2: Dense Point Cloud Generation  
        mvs\_dense \= os.path.join(self.mvs\_out\_dir, "scene\_dense.mvs")  
        cmd\_densify \=  
        subprocess.run(cmd\_densify, check=True)

        \# Step 3: Mesh Reconstruction  
        mvs\_mesh \= os.path.join(self.mvs\_out\_dir, "scene\_dense\_mesh.mvs")  
        cmd\_mesh \=  
        subprocess.run(cmd\_mesh, check=True)

        \# Step 4: High-Resolution Texturing with Seam Leveling  
        textured\_obj \= os.path.join(self.mvs\_out\_dir, "textured\_artifact.obj")  
        cmd\_texture \=  
        subprocess.run(cmd\_texture, check=True)  
        print(f"Textured asset compiled: {textured\_obj}")

    def validate\_and\_filter\_mesh\_open3d(self):  
        """  
        Loads the final textured mesh into Open3D, verifies topological properties,  
        and runs standard post-processing (manifold and watertight verification).  
        """  
        textured\_obj \= os.path.join(self.mvs\_out\_dir, "textured\_artifact.obj")  
        if not os.path.exists(textured\_obj):  
            raise FileNotFoundError("Reconstruction output missing. Verify texturing stage.")  
              
        print("Importing mesh to Open3D...")  
        mesh \= o3d.io.read\_triangle\_mesh(textured\_obj)  
          
        \# Verify normals  
        if not mesh.has\_vertex\_normals():  
            mesh.compute\_vertex\_normals()  
              
        \# Topologic evaluation  
        is\_edge\_manifold \= mesh.is\_edge\_manifold(allow\_boundary\_edges=True)  
        is\_vertex\_manifold \= mesh.is\_vertex\_manifold()  
        is\_watertight \= mesh.is\_watertight()  
          
        print("--- Topological Properties \---")  
        print(f"Edge Manifold: {is\_edge\_manifold}")  
        print(f"Vertex Manifold: {is\_vertex\_manifold}")  
        print(f"Watertight (Solid Volume): {is\_watertight}")  
          
        \# Apply non-manifold vertex filtering if required  
        if not is\_vertex\_manifold or not is\_edge\_manifold:  
            print("Filtering non-manifold geometry...")  
            mesh \= mesh.remove\_degenerate\_triangles()  
            mesh \= mesh.remove\_duplicated\_vertices()  
            mesh \= mesh.remove\_duplicated\_triangles()  
            mesh \= mesh.remove\_unreferenced\_vertices()

        \# Render textured mesh  
        print("Initializing interactive Open3D render window. Close window to finish pipeline.")  
        o3d.visualization.draw\_geometries(\[mesh\], mesh\_show\_texture=True, mesh\_show\_wireframe=False)

if \_\_name\_\_ \== "\_\_main\_\_":  
    pipeline \= ArchaeologicalPhotogrammetryPipeline(workspace\_dir="./archaeology\_find\_001")  
    try:  
        pipeline.calibrate\_fisheye\_camera()  
        pipeline.batch\_undistort\_images()  
        pipeline.execute\_openmvg\_sfm()  
        pipeline.execute\_openmvs\_reconstruction()  
        pipeline.validate\_and\_filter\_mesh\_open3d()  
    except Exception as e:  
        print(f"Pipeline execution halted: {str(e)}", file=sys.stderr)

## **Synthesis and Strategic Recommendations**

The photogrammetric documentation of small-scale archaeological artifacts using wide-angle 4K action cameras can achieve sub-millimeter geometric accuracy and ultra-high texture resolution by following these key practices:

1. **Lens Calibration**: The equidistant Kannala-Brandt model (cv2.fisheye) must be used for geometric camera calibration to prevent mathematical divergence along image borders.5 Batch-undistorting images before executing the standard structure-from-motion pipeline ensures reliable feature tracking.5  
2. **Optical Optimization**: Focus and spatial resolution are optimized by maintaining an exact object-to-sensor distance (e.g., ![][image32]). This balances the camera's fixed aperture with the depth of field required to keep the entire object in sharp focus.6  
3. **Cross-Polarization**: Reflections on ceramic and lithic surfaces must be removed using linear polarizing sheets over light sources combined with a circular polarizing filter on the camera lens.1 This isolates diffuse albedo information and prevents registration failures during dense point matching.1  
4. **Structured Multi-Orbit Scanning**: The artifact must be placed on an indexed turntable against a high-contrast, matte background and captured across three distinct orbits (![][image35], ![][image36], ![][image37] elevation) at ![][image34] intervals.1 To reconstruct the base of the artifact, the object must be flipped and re-scanned, utilizing multi-view bundle adjustment to align the two passes.7  
5. **Advanced Texturing**: Open3D is limited to basic texture projection.44 To maximize resolution, texturing should be delegated to specialized engines like OpenMVS or AliceVision.16 These tools leverage the Waechter et al. algorithm to select optimal viewing directions, implement local and global seam leveling, and apply advanced UV parameterizations (such as ABF or LSCM).26 Setting the downscale parameter to 1 preserves the maximum detail from the original 4K source images.26

#### **Works cited**

1. Introducing High-Fidelity 3D Archeological Photogrammetry Models \- Ancient Cyprus, accessed June 26, 2026, [https://www.ancientcyprus.com/articles/introducing-3d-archeological-models](https://www.ancientcyprus.com/articles/introducing-3d-archeological-models)  
2. AliceVision | Photogrammetric Computer Vision Framework, accessed June 26, 2026, [https://alicevision.org/](https://alicevision.org/)  
3. Welcome to meshroom's documentation\! — Meshroom documentation, accessed June 26, 2026, [https://meshroom.readthedocs.io/](https://meshroom.readthedocs.io/)  
4. Using — OpenSfM 0.5.2 documentation, accessed June 26, 2026, [https://opensfm.org/docs/using.html](https://opensfm.org/docs/using.html)  
5. Calibration of Action Cameras for Photogrammetric Purposes \- PMC \- NIH, accessed June 26, 2026, [https://pmc.ncbi.nlm.nih.gov/articles/PMC4208234/](https://pmc.ncbi.nlm.nih.gov/articles/PMC4208234/)  
6. Small Scale Photogrammetry Part 1 \- Main Challenges \- Pix Pro, accessed June 26, 2026, [https://www.pix-pro.com/blog/small-scale-part1](https://www.pix-pro.com/blog/small-scale-part1)  
7. Automated Low-Cost Photogrammetric Acquisition of 3D Models ..., accessed June 26, 2026, [https://www.mdpi.com/2079-9292/8/12/1441](https://www.mdpi.com/2079-9292/8/12/1441)  
8. Camera Calibration with OpenCV — A Practical Guide for Fisheye ..., accessed June 26, 2026, [https://medium.com/@iamgouri180/camera-calibration-with-opencv-a-practical-guide-for-fisheye-and-standard-cameras-2d75fb2830ce](https://medium.com/@iamgouri180/camera-calibration-with-opencv-a-practical-guide-for-fisheye-and-standard-cameras-2d75fb2830ce)  
9. Fisheye Calibration Basics \- MATLAB & Simulink \- MathWorks, accessed June 26, 2026, [https://www.mathworks.com/help/vision/ug/fisheye-calibration-basics.html](https://www.mathworks.com/help/vision/ug/fisheye-calibration-basics.html)  
10. Fisheye-Calib-Adapter: An Easy Tool for Fisheye Camera Model Conversion \- arXiv, accessed June 26, 2026, [https://arxiv.org/html/2407.12405v2](https://arxiv.org/html/2407.12405v2)  
11. GitHub \- Ikomia-dev/FishEyeModel: Python project based on OpenCV module to model FishEye camera and undistort acquired images, accessed June 26, 2026, [https://github.com/Ikomia-dev/FishEyeModel](https://github.com/Ikomia-dev/FishEyeModel)  
12. Photogrammetry tutorial 3: turntables \- dinosaurpalaeo \- WordPress.com, accessed June 26, 2026, [https://dinosaurpalaeo.wordpress.com/2013/12/20/photogrammetry-tutorial-3-turntables/](https://dinosaurpalaeo.wordpress.com/2013/12/20/photogrammetry-tutorial-3-turntables/)  
13. dataset.py \- mapillary/OpenSfM \- GitHub, accessed June 26, 2026, [https://github.com/mapillary/OpenSfM/blob/master/opensfm/dataset.py](https://github.com/mapillary/OpenSfM/blob/master/opensfm/dataset.py)  
14. 01: Environment Setup and Photography | Turntable Photogrammetry Tutorials series, accessed June 26, 2026, [https://www.youtube.com/watch?v=oeyH2w7G8RE](https://www.youtube.com/watch?v=oeyH2w7G8RE)  
15. OpenMVG (open Multiple View Geometry) \- GitHub, accessed June 26, 2026, [https://github.com/openmvg/openmvg](https://github.com/openmvg/openmvg)  
16. OpenMVS Open Multiple View Stereovision — openMVG library \- Read the Docs, accessed June 26, 2026, [https://openmvg.readthedocs.io/en/latest/software/MVS/OpenMVS/](https://openmvg.readthedocs.io/en/latest/software/MVS/OpenMVS/)  
17. Options for a photogrammetry based service? \- Reddit, accessed June 26, 2026, [https://www.reddit.com/r/photogrammetry/comments/1n4ex0m/options\_for\_a\_photogrammetry\_based\_service/](https://www.reddit.com/r/photogrammetry/comments/1n4ex0m/options_for_a_photogrammetry_based_service/)  
18. GitHub \- mapillary/OpenSfM: Open source Structure-from-Motion pipeline, accessed June 26, 2026, [https://github.com/mapillary/opensfm](https://github.com/mapillary/opensfm)  
19. Building — OpenSfM 0.4.0 documentation \- Read the Docs, accessed June 26, 2026, [https://opensfm.readthedocs.io/en/latest/building.html](https://opensfm.readthedocs.io/en/latest/building.html)  
20. OpenSfM 0.1.0 documentation, accessed June 26, 2026, [https://opensfm.readthedocs.io/\_/downloads/en/stable/epub/](https://opensfm.readthedocs.io/_/downloads/en/stable/epub/)  
21. Texture Mesh gets stuck at "Assigning the best view to each face completed:" · Issue \#620 · cdcseacave/openMVS \- GitHub, accessed June 26, 2026, [https://github.com/cdcseacave/openMVS/issues/620](https://github.com/cdcseacave/openMVS/issues/620)  
22. \[Photogrammetry Testing\] COLMAP 3.7 and OpenMVS v2.0 \[now ..., accessed June 26, 2026, [https://peterfalkingham.com/2022/02/05/photogrammetry-testing-colmap-3-7-and-openmvs-v2-0-now-with-cuda/](https://peterfalkingham.com/2022/02/05/photogrammetry-testing-colmap-3-7-and-openmvs-v2-0-now-with-cuda/)  
23. Releases · cdcseacave/openMVS \- GitHub, accessed June 26, 2026, [https://github.com/cdcseacave/openMVS/releases](https://github.com/cdcseacave/openMVS/releases)  
24. cdcseacave/openMVS: open Multi-View Stereo reconstruction library \- GitHub, accessed June 26, 2026, [https://github.com/cdcseacave/openMVS](https://github.com/cdcseacave/openMVS)  
25. CLI Tools · alicevision/AliceVision Wiki \- GitHub, accessed June 26, 2026, [https://github.com/alicevision/AliceVision/wiki/CLI-Tools](https://github.com/alicevision/AliceVision/wiki/CLI-Tools)  
26. Texturing — Meshroom v2023.1.0 documentation \- Meshroom Manual, accessed June 26, 2026, [https://meshroom-manual.readthedocs.io/en/latest/feature-documentation/nodes/Texturing.html](https://meshroom-manual.readthedocs.io/en/latest/feature-documentation/nodes/Texturing.html)  
27. openMVG\_main\_SfMInit\_ImageL, accessed June 26, 2026, [https://github.com/openMVG/openMVG/issues/650](https://github.com/openMVG/openMVG/issues/650)  
28. Can't run SfM\_SequentialPipeline.py · Issue \#1218 \- GitHub, accessed June 26, 2026, [https://github.com/openMVG/openMVG/issues/1218](https://github.com/openMVG/openMVG/issues/1218)  
29. A \`tutorial\` for \`colmap\` to \`openMVS\` · Issue \#692 \- GitHub, accessed June 26, 2026, [https://github.com/cdcseacave/openMVS/issues/692](https://github.com/cdcseacave/openMVS/issues/692)  
30. \[OpenMVS\] TextureMesh creates black artifacts/patches on the object surface (masked dataset) · Issue \#1251 \- GitHub, accessed June 26, 2026, [https://github.com/cdcseacave/openMVS/issues/1251](https://github.com/cdcseacave/openMVS/issues/1251)  
31. nmoehrle/mvs-texturing: Algorithm to texture 3D reconstructions from multi-view stereo images \- GitHub, accessed June 26, 2026, [https://github.com/nmoehrle/mvs-texturing](https://github.com/nmoehrle/mvs-texturing)  
32. Gibson Env V2: Embodied Simulation Environments for Interactive Navigation \- Stanford Vision and Learning Lab, accessed June 26, 2026, [https://svl.stanford.edu/gibson2/assets/gibsonv2paper.pdf](https://svl.stanford.edu/gibson2/assets/gibsonv2paper.pdf)  
33. 16.74. texrecon — Ames Stereo Pipeline "3.7.0" documentation \- Read the Docs, accessed June 26, 2026, [https://stereopipeline.readthedocs.io/en/stable/tools/texrecon.html](https://stereopipeline.readthedocs.io/en/stable/tools/texrecon.html)  
34. Labs AV Texturing 5.0 geometry node \- SideFX, accessed June 26, 2026, [https://www.sidefx.com/docs/houdini/nodes/sop/labs--av\_texturing-5.0.html](https://www.sidefx.com/docs/houdini/nodes/sop/labs--av_texturing-5.0.html)  
35. open3d.t.geometry.TriangleMesh \- Open3D primary (unknown) documentation, accessed June 26, 2026, [https://www.open3d.org/docs/latest/python\_api/open3d.t.geometry.TriangleMesh.html](https://www.open3d.org/docs/latest/python_api/open3d.t.geometry.TriangleMesh.html)  
36. GOATEX: Geometry & Occlusion-Aware Texturing \- OpenReview, accessed June 26, 2026, [https://openreview.net/pdf/446ba416b0ac0c92aeb5b874ce393748157b52a1.pdf](https://openreview.net/pdf/446ba416b0ac0c92aeb5b874ce393748157b52a1.pdf)  
37. GOATex: Geometry & Occlusion-Aware Texturing \- arXiv, accessed June 26, 2026, [https://arxiv.org/html/2511.23051v1](https://arxiv.org/html/2511.23051v1)  
38. GOATex: Occlusion-Aware 3D Mesh Texturing \- Emergent Mind, accessed June 26, 2026, [https://www.emergentmind.com/topics/goatex](https://www.emergentmind.com/topics/goatex)  
39. Mesh \- Open3D 0.19.0 documentation, accessed June 26, 2026, [https://www.open3d.org/docs/release/tutorial/geometry/mesh.html](https://www.open3d.org/docs/release/tutorial/geometry/mesh.html)  
40. Mesh \- Open3D primary (252c867) documentation, accessed June 26, 2026, [https://www.open3d.org/html/tutorial/geometry/mesh.html](https://www.open3d.org/html/tutorial/geometry/mesh.html)  
41. Beyond the Surface: Advanced 3D Mesh Generation from 2D Images in Python \- Medium, accessed June 26, 2026, [https://medium.com/red-buffer/beyond-the-surface-advanced-3d-mesh-generation-from-2d-images-in-python-0de6dd3944ac](https://medium.com/red-buffer/beyond-the-surface-advanced-3d-mesh-generation-from-2d-images-in-python-0de6dd3944ac)  
42. open3d.geometry.TriangleMesh \- Open3D primary (unknown) documentation, accessed June 26, 2026, [https://www.open3d.org/docs/latest/python\_api/open3d.geometry.TriangleMesh.html](https://www.open3d.org/docs/latest/python_api/open3d.geometry.TriangleMesh.html)  
43. Surface Reconstruction — Open3D latest (664eff5) documentation, accessed June 26, 2026, [https://www.open3d.org/docs/latest/tutorial/Advanced/surface\_reconstruction.html](https://www.open3d.org/docs/latest/tutorial/Advanced/surface_reconstruction.html)  
44. Adding Texture to a Mesh in Python Open3d \- GeeksforGeeks, accessed June 26, 2026, [https://www.geeksforgeeks.org/python/adding-texture-to-a-mesh-in-python-open3d/](https://www.geeksforgeeks.org/python/adding-texture-to-a-mesh-in-python-open3d/)  
45. Adding multiple textures to the mesh can only display the first texture · Issue \#6954 · isl-org/Open3D \- GitHub, accessed June 26, 2026, [https://github.com/isl-org/Open3D/issues/6954](https://github.com/isl-org/Open3D/issues/6954)

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACcAAAAZCAYAAACy0zfoAAABtUlEQVR4Xu2VvytFYRjHH0khP4uUsijJYEA2Sikymf0DBhlMUhilKEpIiY1BCGFgUBa/wmAxKCkxUhaDX99v7zk89+m9R2dhOZ/61Pt8z3Pvec59732vSEJCgpciWAfH4LG5FjILr2EHHIFv8COlQ6QQXonrIw3wFuZ+d4j0wAlYBnvhtLrm5RM+iXvTdMO9wkpV94t7XZPKZoKsXmUtcFzVW2pNRsU9RFoqYCbsk/TDLZo6R9wDramMD3Cn6pAXcf1kUF8A7bDbZF6ihuMn8myyffigavbsqDqE+XCwnoOtwboKbsKsoI4karh7+bkByYCPcE9lHGJd1SHMF4J1NpwS9zruRmnY9BtRw1naxN20U2WsV1UdwnzDhnHhcCc29BD+GA5MHjWcb7tjweFObeiBx8iupB4RJGpbV2wYFw53ZkNDLVwW/5eYQ2zbUFw+acO4cLhzGwbkwUtxZ5nmQq05xI2qQ5hX2zAuHE7fTMNtPBR36DaLO1x5Ri2pHv47vMNilZXDI1XHhp8Kf9I8g3iI1sCClA739D6HVA/PL7uF87BR1f9OCRyAXTDfXEtISEj4K74A26Nh29f0K8AAAAAASUVORK5CYII=>

[image2]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACMAAAAWCAYAAABKbiVHAAAB50lEQVR4Xu2VTSilURjHHzYiH1koaYYNZZQkNdQol3yU2FiRBitZ2CjLWSAfZWFhdpSsfC2ImaJQltIUNhZjQQopkpjFFDP+T+d5733e4773elnR/dWvznme03v/955z3ksUI8Y7pNwuCHGwC+7DYzgNc1XfoQ5uwUv4A5a4ukSpsAomwmKY724TZZJZMAv73K0gU/AXrIDZcBLewDK9CPyD32ACHId/YYPqD6gxw5/p4j88gufkHeYMJlu1JXig5h+k5sC/5g68UrUFNWYWrXmQn+Qd5g7mWbU2Ml/E4TcMqDnTSu41n8hsEcNhm1TPRaQw/MBTWK9qm3Bdxilk1vA50DRKXbMGl0VPIoW5J/NQNgN+hycwR/qF0iuQuUOt1DmsLyKF4Z90gkKB2BmYJP0aqdm3IyB13h5fcJh+uyjwNT2En+EDhQJtSJ9vY7gwlVK3z1tUOIx99Rz4RnyU8RcywZxATKmM7W2qlnqWVY8Khxm0i6CTTACbNPhHxvHwlp7epq8UCuwLDjNkF0E7me0Jx64ar8JmNWd66RVhhu0imdd+uHo6mfePQwscVXOGD7mvMM7e22rGyBzcPTgPr+EKmUCabXgBR8j8XczRC671c+BD2AG7YZG7FYRfAXyzesh7TYy3ySO8aWzMS3j3PAAAAABJRU5ErkJggg==>

[image3]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFUAAAAaCAYAAADG+xDjAAADVklEQVR4Xu2XWchNURiGX/M8Dxnzk5lEZiWUxAX9SUnixpAxQi64QoRLEREpU4kr3Cg3kkJCuEH6kzGSIjL73r69Out8/z5777PPPhf691PvxXm/vcaz1vrWAnJycnKKaCRaIepsAw2MlaLu1kzLcdEZa6aAf87/zALRE1EvGyiXaaKJ1gzgyh0uqhX9FT0VTfHi/QL/CrRDbb1YFJz8PqJH0PJU2ArpL/og2iwabWJJYZ++i26JVolGiGoCsV62vTz4ljSDjjM1HNw9a5aAjX8TdfK8bqK13u9y2YTCpIYxWzTQmmXiFkRj408WfRXtND5ZIxpnzaTMRekBWdzgNwS/W0P//UroLfqN8D5wh7y1ZgqOia4abxB0B4S1Szi2C9ZMQnPoyrtmAyXYhcLEnoJu+aZFX6SDyYF1Lva8m9D2KmWA6LrxOGFs776onYn58Jul1oxjPLRg2PIPg+fbH2iZ26I2xeHU8Nz+IbrseVwl1Uh6TUSXRC8Qn4w4ziPWjGM1tOBCG4iAq5plOMFZwgn9Keoq2gFdTdXgMLT/TFZx8FjijikL/gtsIOmBPEn0TvQeKRqLgRmafWHi4A6qBtxl1CIbKMFz6PFYFuegA+GhnYRXopmiPdByI4vDFcM691ozI2ZA699q/Hnmt89daJmyjiFe9pNOTg8U/mEe/ix3oBCuGF7NWOcsG8gAju+T6JANCGet4fEYKVbqUehAptqAoT3q32VZ7qOopfHTMh96pmaV/By8sjEpsb9MUjYWNWmvRW+sGQevMGyMr4xSXBSdR/0t4O54N4zvw6TAe+Z6GwjhoWi/NWOIq5svI/bxGXQn+LiX1Dbj+zAetZJDGQwteNL4zMB8Ei6Dxnlf7OjFW4juBDGKZ3LYfc/Fv9iAR1/RHOh326HP3iRPXe4QV3crE3OcgK7+JdAkS00XbUGhb0PdxyEwvtGaSahD/XcuV59r1InPSQcbsvHdXtzBl8xnRE+qrYfaV/RFaVzdQ2wA+gTlhNq6nX5BF0YU/G6UNZNQA22gWvCMfGnNjHB12zd9FoyB7tTUHET2CcKxDuFZNwuqWfdpVPgE7wC9e2bNMOjx0tP4WVGH6tQ9AdG3gsSMFT0QdbGBBgZvOqmSU05OTk5ONvwDqn7D7VsqE4YAAAAASUVORK5CYII=>

[image4]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAmwAAAAwCAYAAACsRiaAAAAEgElEQVR4Xu3dWah9UxwH8CXTg4wZUuhPylR49KCMGfIkHhQiHkR4UIiUIVKGUJQxf0NI5lnEgxdSyjzW/wEPhowPxrB+7bXdfdY953/3Oec697r386lve++17jln9T+39q+11r7/lAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACY77qcr3L2qDuW2BV1wxJ6JefcuhEAYFYeL8e/B1qX1gs5V9aNS+S+cnx/oBUAWFE2Sc0s1nL3e92wRDYux+VSsLWF7Iedti875wDACvBrdX1mWtzZrF1z3si5o+4Yw8d1wxSmHc/d5bhYBdsBOd/lnFh39NR+V/V39kV1DQD8T12cs3fneuuc3dP8m/8oT9YNI8Ts2I51Y093luOabuMIsxhP2Cr1K9j6jqfvv/cwP5Vj/R73V9cAwP9UfZMP4xRsT9cNI/R9v2HitW0WMovxhE9SUyhtV3dUZjGeDXPeydmyat+mugaAVSX2Cu2S82bOfjm/DXYvOzHezXN+zFmXmqW3q0vfsEJhnILtmbphiG1z/irnT6XR731vzoE5n+UcnfP5YHcvizmeT3MuSc1m/n3S/KXjPvqM57jUFFwb5Vyf89pg97+if9zx7FU3AMBqsH3Opjmb5fxZ2qLQ6CtuxjvlbJDzXNUXjkijC4hJtOMNUVjGUt5NaW5maNhnLXbBdlvOzTkXlOuTynGHnEfLeYg9ZRfmPFKuH+v09TXNeF7N+Sg1302Iwvb5nLNTUyzdXtrH0Wc8sT/vtJzDynW7jBqzc2+nuYcc7knjj2fSfXEAsCK8lXN43djDUakp2Nanb7E0rmHvO6xtsQu29r0eTPP3fdWv7/u5o9TvN8yw8VyWc2Q5745hluOJGb32dyqKtD1zds55uLSFccdzTN0AAKtB3OB/SYM3zofKMZbXYvYmtP3tstXP5Rj9UbDFhvcfck7IObkc15SfGfemvD7teM/K+aC0nTfXPfSz/quCLZbzLs15oNNXv77v545Sv98w6xtPfDftdfy5k3bpdFILjSeeWG1/N17OOSjnrnId39m35bw17nhiJhgAVp3Y2P1NajZ0R8F1S6fvxs75bjlPpLni4KpyPD7NzbDF68PlqVkajBt0mLZo6WrHe2hqCst1qdnD1WqXdVsxAxif3+bggd75FipI9s+5qHP9dec8PNs53yLn1s71JKYdT+xLbB2Sc0rnehILjeeMNDerFsvV8ec9uk/thu7fnxtnPPvWDQDAYMH2ejlG0RMFwtpyXRds75XzeCgg9iaFxSzYFhIF2ul14xhiz900hu3jm8Y042mLx7XdxilNOp4Xc44t55P+PsSTrABAJTb1t7NkL+Vck3N+ajbSn5pzQ861OX+kpiiIG3EsP8Z/cxSvi5mwc0r7LH1fN8zIu6lZ4muXlJdSbOBvZxVjo/9yELN98YRvLM2OK5ZC44lTAGAFiYcoWDkWWooFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgLH8A7rF3KtiQ4w2AAAAAElFTkSuQmCC>

[image5]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAmwAAAAwCAYAAACsRiaAAAAEXElEQVR4Xu3cS6huUxwA8JVnQkRioFwUMfNKeZSByEgGxIAoAzOEgYHJHQihlBmKMCDPwkz3euSVZx555kZCBgh5hvVvr93dZ51v329/3z73nPOd+/vVv7XXf93z3fXtc2r9W9/aX0oAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAALPddjnPr5Bp7oU6soQtyPFsnAQBWy6ul/XtJdu29XCfWyHE5Ts3xfj0AAGws39SJdei/OrGGokBaLwXbHzkuzPFbJ3dbjn06fQBgwX1S9Q/N8WeVG2PfHA/k+KwemMHjOXark3MaO5/nSrtSBdvY+fxQ2qdzHNzJ/965BgAWWBQLj1S5KNiG7mZdWyd6vJLj4jq5E5xQJ3qsxHyGFGyrcX9uLO1LS7IpHZPj1ioHACyg2JU5pE6m4QXbdXWix9DXm+TT1Pz8kNc4qU70GPJaO3J5jn/S9AchVuP+hCjWzq+TafzrAsBCuzLHUzmOL/0ofObdIdnZYq4HpaWLd3vdt6D35WvX14ke7etFYXFTd6CyX46fc1ydmn+759LhqU6uEz1Waz7z3p/LOmNdN+T4PMd5Ob6uxiYZ+nsEgA0pzhzFYrhH6Q9dGA/M8Ve5vijH2Z2x1lU5fqqTI8RcT8zxbemflmNbue6bd1++NqQguSTHuzkeLv04jxZ2z/FWuQ5HpuYwfzvPZzpjQw0p2Prmc3uO73McW/orMZ9570+c14t+3J/4iDpcUdrHSvtEaXdk6O8RADasbaXdO822ML5WJyZYyYItdOcXh9GPmpDv6svXhhQk8Vp7paYQrc991f/PrzkOq3KzGFKwTZrPAWn714d05zR2PmPuzzmlje+ga0WxPYv6/gLALufe0t6X4/5yHYtr+9Rlu1h+WNp7ShsfsYVYfK/J8XHpv1fasDMLtu71v53rrqEL/dCCJJyRY0uOIyaM9fVnNbRgC5PmE9od0DB2PvPen9hhOzNt/1tpPV/1pxk7fwBYeLEb8lVqDp8fXnLx0Vbr9NR8bNUumu35pw9KG6Jgi8X5obS9cAsrXbDFXH7JcWdauojflZYf1I/xNrYuHVpmWkES7y3O97W+yLG5068Lijer/qymFWzT5lN/xcnY+Uy7P2FH8wnde9TdbRuiW3wCwC4nDn+3ugtqW7DFk5e3lOsYj69e2FT6dcHW/vwdOY4u1ytZsMVcHyzXW9PyhyO+rPqziG/ZH6Mu2Mbav07MoN0x3dRNjjTm/kQxHea9R5fmOKtOAsCu5MXU7JjF7lqcYQtxSD0W11NK/+3UFGGxgxIPFzya4+bUfEFq7JR8lJpD7rELc3dqDri/kZqPV+ddpCeJucZTovGkY8yhFoXBmEJnXvFe432+Xg+sgdgh7e4srgdbUrPjN+8Zuh/rBACw2J6sEyy0d+oEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIz1P4Qn3HfZX1AAAAAAAElFTkSuQmCC>

[image6]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAG4AAAAaCAYAAABW6GksAAADEklEQVR4Xu2ZS6hNURjHP2955TEw8AoZIJRHBkoeeRQpCgOlFO7AI8oIg5MSETIzQFeiPCdCSCJlQB4JSdgKeUcYkNf/37d35zvrirPvWdtZaf3q193rW+vsu85ee6/9rXVEIpFIuExO//aH92BHUxcaS+E62AKehp/hsIoW9acD7JseT4X7TZ03OkvliX/ChaYcGtfgA9geDhXt796KFvVnpugNlsE+9jNlL3SDZ02Z/2S7KYfGZfgOdoIt4Xd4vaJF/ZkC15oyr+ksUy4EXpQebjBQVotelGyqDxHODJfcoG8mweluMGDewA1usEoWwLZusADYvz5u0Ce94RM3GDBt4CY3mIOHot+5SKbBxA365KCUn7QJcE25KkhWwVJ6zKfmeLmqah5LsQN3XsoJSQmOLldVx0X4AZ6BM+Bt0RS6l2nDJUBj6i0429T9S5jNsn9X4XjYE76HN+GotA3T69eifWU2fA7uTOvykEjzBo5LJU7Rd+A4p44x0hpeEO3jPvhcNAnMxRLR9JQvcQ7QWDgXbk3reVewzlqPdVFJ9MsOhIfhJ9FBHCw6hXMwySNp2t8VaV0eEmnewB2F7eAP0RsqY4Do9Et4A9r+vc0aVcvi9O9G0RNk7IDdTTkEFpnjA6L95U03T3QqHGPqfZBI/oHbLZrUMOFg/7aZukOwwZS9wLWPHbjQeSraXz59tbIefvuNPL8boyf0Y38kEf38cBN7ITo7eIPbL1/hF7ciYHhRis5wE8n/xGWwf3dNeUga8wpf5jxp4YtAj7C/jW7QM4nUNnCbTXlZGvPKFdGTTnQrAqKLaB9Xim5l8Th7p40Qvci+F8uJ1DZw2fKJmS+TD+8Dx2mS6T8zoVDhdH5KNGXeI3oRlov+AnBfmqbdPkiktoHbBVvBG2k5d+b4N17BLW4wQJjm88uzr0zvmaC8hCNtI48k0vyB4wYAU/+P8IjowB2raBEpjPmi22Z54K8R3BGZY2Jczz0T3UyOBMog0aeLO1CEA88lBPckIwHTVTRf4LuX0+xJ0Q2CSCQSiUQikf+TX6a0rXIwjsRWAAAAAElFTkSuQmCC>

[image7]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAB0AAAAZCAYAAADNAiUZAAABkklEQVR4Xu2UyytFURTGlzzymCDynIkyEyMyMjCUFDMlJcojJoyUjDxKJkYMJSViRClhoGToTyDyKikSA77P2s5Z59wb7sXs/OpX51t737332XufKxIR8cfcwz1YBSfgG+yzHcAyfIAtMAUewTNYZvr0wiKYB4dNPYYC+ATzTW0fPptMuJBBk0vgC9xyOQdu+M0f1ISyx5ToJJZR0UkszPatyKGrkzo4ZtpIdyh73IhunaVNdLBcl1tFjyDMggQXt2SeK2GayQHu4Eqo1iE6WK3LQ/Dab/aYk+Ck2XAbrklwATGcwvVQrV90sCaXx+GF3+wxI7HH8CNKRbcu0+V0eC46WKOrTbpamGlJclLyKnquPMNFuCk6WIVr5wWJ96az8otJ6+EOvII94p8pv0fSCW/ds2Vekpw0FY6IPwFZleBgvIXMhaZGdl09YXhZ+MMGl4vhIzzweijs02wyF8sbHW8HvqUanoj+dZFjeAnLvR4KLxsXkuHygOhCuj47JAq/Rw7Cbf6KLNguerG4IxEREf/LO0J7UdUkcnfcAAAAAElFTkSuQmCC>

[image8]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAbCAYAAABFuB6DAAAAtElEQVR4XmNgGOaAA4ifAPEzIJ6EJgcGzEC8G4jfIYmtBmJOJD4Y1AHxfyAuRBKbC8TmSHww+AbE74GYG0lsHRAHIvHBAGTaTDSxq0AcjCwQA8RfgJgVScyMAaJZBEmMYT4Q/wPiH0j4FwNEIQq4DcQ9QKyBhM8zoClkZIDotkMSEwTi3wxoCmXRBYDgEFTMA1kQFKB/kQUYIIpAQYMBziKx2YD4HgPEeqwAFr9z0CVGwQAAAIlDJ0MkTwoxAAAAAElFTkSuQmCC>

[image9]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAmwAAAAyCAYAAADhjoeLAAAFlUlEQVR4Xu3dV4hkRRTG8WPOihEUddUHURRzQFFRMSuGBwMiuojxwYCCYMAFRdAHEVGMqPggitnF1UURV8QMBgwYMKFizgGzno+qsqvP3Jm5t6d7d9z9/+DQVafu9u2+PXDPVFXPmgEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIHM8bv8fxRoGAACwCFkpJgAAADC9PBMTAAAAmD7W8dgzJlt40eO+mByhXT0+9FgsDgAAgHaejIkhOSAmMHQ3eywek5NYPj8e4XFePTBCP+fHH/qyAAB0sK/Hkh7/xIEFbOOYGNDnHtt4PG9plqP2a+h3pWs202M9j3Vz/7Q8dpXHirk9CkfZ9PvM5qdlPE6JSbe5petyS+5v5fGXx6EeS5WD3B4el1f9QazqcYOl861f5c/3uN9jRu6vmR//zI8AAHSi2YZfcvsTjyWqsQVpWY+DYnIAu1l/4acbq27UomWqk6uxQagoK773uLXqy0+hP2yLcsH2UExU7rBUpIkK9ia/x8Q49ouJBvocVq76On+TURbwAICFWH3DV3uYBdu9Hh9b/431JUvLQ7M93s05FY1venzncU7O6bWUKK6zdPOtZ1VeszRLpqUxLTcdW43JWh6vVH0938FVu7atx00ex3v8aGn2pI3lLD2XzhW9Zd2X7EQ39voalDihaoset/D4wmNuzolmn97w+NRjy5zT7KLe45fW2/el477yuDv3B6HP5CyPbzyuDmNTpZ/HpzxWD/mdPTYNuUjX5tKYzA7Lj3XBPZ42BZuufZk90/WNNMu3gsdtcQAAgMmsbemmpoJHEQsY2cF6401RZquiVTz+zm0tQ23QG/rvPCoytAm79Ov2yzZ2hq2M3eNxTEM+tiPNttVLUvHYB3JOhZpe++n9w+PSv9kuJrMbPfaKyQ7qwkzFldT7oJQvheKzHgdW+aK0tdFeRbQK1ovD2E4eT+d2F6Xg0fNoT1i8pkX8ualjIo9bKnLeC/knQr+JCnUtU0dl6VrRZp9hm4JNf1pEz/dByBflfFqWBwCgk3M9Xs3t4yzNkAzTRh6Penxm6WZe1Df1KzzeqfpFU8GmQko3Yc3QXVPlm4qTSDM1v4Vc07FNuYloNk7XrlAxWdM1nhlyXZTXc6fHXbldFxn1651raYn37JwvBdEflvZSqaDTfsUiHjfo/ioV9U2f4bCsZml5syw5aq/Y3r3hRmdYmpWLexbb0HWoQ+cubc0Cj0fXcpDZVAAAJnS9x5m5rZuRbozDcqKlPXHFkVW7LjKutFTQRVo6PSS3tWFbG8nLnqRLPK7NbWlTsH1btTXTJk3H1s87me2t/zlUoGrWsqYZqLpI6krfYizLvDrXBdVYyRUPWirYNDNYZjdrKth2r/rjHdfVI9b/+Y7C1x6zcvvteqCBrvcmud30GXfVZoZNs8jDOBcAAGPsY72CLW6Wn6rnrHeD1XLR0db71l59Y6uXQUV7tET73jR7pZkxLQVeZml5TOZZ+mbe+7k/WcGm/Wi7WCrU9E1BLf9JPHZpa/4vg+Z57B9yWobUvy/LlJpZic8nj1na4zYVZeZTs0Uf1QPWf05ds1Mb8trjptf3go1dwq6Pe71qd9H0vodtQ0u/VOgLJBMVUFtb/2el13ZR1R/EROcrLrTmXzwAAID1CiZ9caG0VXi1odkqzZK1Mehy8SiLmfI+9b71/lX8LsxLcg9bms2b39oUbAAAYITa/mmHQf78x+EeO8YkBraZjf22KAAAWATM8DgpJoNZMdHSnJgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEwD/wJgVDAEOC642AAAAABJRU5ErkJggg==>

[image10]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACUAAAAaCAYAAAAwspV7AAACR0lEQVR4Xu2VzYtOYRjGL98RYrBBWZAoisUQYYPyBxApGQmJLCajLPgPRCFFTCKxY8GCknysNJOFr3zUWMwQoZSRSbgu93Pmvc99Zk5z9Fp5f3XV+/yej/O85/k4QIP/mHXM4ihLUPvmKOtJC/OMGR98GbOZniirsoD5xbwOfipzILiMhcxb5gKzCNZ/a64F8JgZFVwlNOjZ4I4xE4PLeMM8ZEam8kvmUa36Dz+Z1uAqoUltceVpzDdXjqj9MlfugE3CcwO2jKODHxIa/FVwtzH4pJ4w21x5DPMDNlHP3OTOBT8gc5h25jOsw2HmjKsfznxh7jqXsRL2oEnO6WTKxUmJ98zzKCMbmF7mEuxE3YL9y82uzXzYA045l3EaxYfvTq47eHEHxWXNMQ7Wea1zS5PzbEpuf/DTk1fmuehPym2vNe1HKxHHz7EH9jq1PBkHUey0K7kdwa9Ivi94Oe2/puDFERTHz6HN2x7cTRQ7aTJye4PfmHxn8HJ+T3pOojh+Dq253kKGLravKK659pcGOhS8rgz5i86Nhb2lWc55tHdLJ3WNWeLK12EdTsD+6c7kZyR/OZUzJsOWLpuU9thHZkR/iyK6UEs/OauY4+m3HnwftUl1MRNSndBAchHd+h+YmbBlvJevzqHTrZN9NVZE9D36xDxlhjFHYffVGt+InMfAr10P0pvqgt1vZbf1atgY+2LF36IT+iLKiryDfbDrynpmeZQV+A77etQd7ZmyjTwYOhRtUdaLKcwD2CEZKrqkr0TZoMG/5jcoaoVvYrsnfwAAAABJRU5ErkJggg==>

[image11]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAmwAAAAwCAYAAACsRiaAAAAFn0lEQVR4Xu3cachtUxzH8b85GTJlSFy8UuZQXqAMCUWGawxdGUKSV6JImSJDpkRIphRRhuKNzKIokkwhJEMyk5n1a63lrP2/e989nKf2Ped+P/Vv773Wec6zz/PsOr/WXmubAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMCs2SPUm6FW8x0jOTPUM6Ge9B0jWS/Uv6n0d1oeXBfqDt8IAADml4KIfFBpHY8C2/LktLQ9sNI6nkNCHRvq0FAbuT4AAObOy77Beck3zLFvfMOITknbzyqt41vJN4xk31DHWQy217s+AABm2o42GUmS7Yr97P1QG4a6uWj7q9hfKBeEOibU5aEWub4hjrfqZ1uWNSwGoVVt6dt7f7jjoTTyo/PZ3Hc0+Nni7dj8GXIw6vqZ2mwd6tVQt/uOBo9avF6eC7VKaltn0j21tULdbd1HNOuul0tDLQ51Tn4RAADzYG2rBgAfBu4LdXTaL/tODXVQcbwQ3kpbBYkXyo4ar/mGBv7zNKn7G/jtsvzgGxp0eS9RaNky7X9iMVD+k467vIfCVRcKo5v5xga3pO3JFoORXJi2bXbxDQ00uqvbml3462X1UFeFuu3/VwAAMCeuDnVT2tcIzttFn9QFmexXdzwNzYNSKBHd1vqw6KvTJbBpTpP/PE2eKvbz5zwr1DsWg0Cbn3xDDU3Sz6Grjf+7b2ExXOvzaLSzzeO+oYH/nza5sthXILoz7S8p2pdlV9/QoOv5NF0vui7qRokBAJg5a1oMWzuF+jvU+qn9xFBn5xdZnAeURzHEf5n642mUt1iftkkgaNIlsOncj7C42lNf8LrFWOcwm0xSVzgb8rma3rukYHxjqE0szrP6qNpdkUO0DDmfJ3xDDX3mHCAfC3WXTUb1vPIcdO3oWuljN9/QIP8ejZhdFOqkoq/U93oBAGDm6Etx5WI/u8aqtznVp1GmbVPdWvTJkCDRRO+Vf4/22+Z5dQlseh/NZ9JIzMahrkjtS/ILEgW7/LvvDfVutbuTLoFN57O3xdEyuSdtX0mVHRlqd4vno7A55O/cJbBppEzzEs9Lx/ln7g/1usVgmfn/T19dAptGyt6w+PvlYZtcp5pbqEUFmT+ftusFAICZovlHOVwcZdW5YteGOrw4Lr+Yy5G2bMgXd5P8Xgorz5cdDdoC21ahfkn7/jzLxRNS9vvXdtU1sIlGh3R7U561yS3OH9O2nIOlOWZ59K+PLoEtn88DoS4r2g9I2y/TVnPcvk/7GvnL89f66BLYdD4a4Twj1ItFu0LbwaH2L9r6Xi8AAMyU7W0S0r4LtU+oT9OxVjHqNlT2W9pqJaDmcnlDw02d/F5d37MtsGm14flpP7+nJu+LD2z5MSYPWbxNPERbYFNQzvPk/rQ4YqTVt5kWdpye9nNg2tkmo0199QlsWjhwsU1uc+5lSy+iyIFt6LzFroFN9rT4gOBFFsPagxZ/vi6wdb1eAACYObq1qeeL6dbct1a9nZS/mEVz3b6w+PR4TwsUdNtsoexn1duCbdoC28c2eQzGYqs+T80HNvkq1Da+sYe2wKbVtnk15g4Ww/K66Vjn6R+todGtaR6U2xbYFAb1WIzsa4vz/UplGDo31CPFcV9dAlu5slWLCC4pjn1g63u9AAAwV9qCR6ZJ3nmxwhi0UGCousA2rRN8Qw85EJcrVaeVR+mGuCFtF3L0atrnten/XQY2AABWaF0eYSF64Oos0hys3y2O4Gzg+sag26IKRqoclMam25HvhdrUd4xII72f+0YAAFZk/kn/Xt0CBAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACYSf8BZ+L/zO6cwLUAAAAASUVORK5CYII=>

[image12]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADAAAAAZCAYAAAB3oa15AAACI0lEQVR4Xu2Wy6uNURjGHySOKMlA5xycIrfEX3AMUCeiKAOlXBIGSJTUGbgkA9MzOCam50xkQExELmVggDIQJROXXEISueTyvN61nXc/Z+9t7a/4Jt+vfu1vPe9a3957fWutvYGKin/CArpew/+IvX9huukODUvgHd2iYQ6XNSiJbfQTnauFVqyjPzUsifH0KT2vhWYshn/4Q1ookR60MaGH4Z17tVAyzzRoxkX6hU7UAllF79NTdGzIl9E3oZ2DrekP9CqdkTKbtJd/etRzBiP9mjIBPvs3tQDPVqZr67Mx1F6kLJcj9BjdCx83kPLZ9DXqJ6fGPmScivYN7YYXtEAepNfJ8Cc0NbUXwcdkP2LyiM6kN+Bjl4fa8XAd2YyMfTkffsMhLQS20rOhvRs+ZjhkufygT1A/4wfDdWQtPaqh0gn/MFe0kJgEn/0pIXsOH7MwZLnYuL7Qnga/XyN20l0aKuPoN3pHC4mlGL3WrV3beNdCnoONrS1Fo5+eCO2ILZ8NGjbCloLduEdyYwx9CN9stuFrm/ASfP90jXT9nZutjmOr2+Y0btM1oabcgr//X7GfbrvxJi0k5tC38FkfpPvpK4w+Rt/D/8e0euw224/h41dILdJBv2rYDFuHn+lpLRTgJN2uYQHs+Nal25JZ9KOGbbKE3tOwAPPod/gx2hZ74KdSUe7S1RoW4Bwa/y5lcR1+MhXhgAYFsb8u0zWsqKio5xcx6maX6HAefwAAAABJRU5ErkJggg==>

[image13]: <data:image/png;base64,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>

[image14]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAC8AAAAaCAYAAAAnkAWyAAACKUlEQVR4Xu2WTYiNURjH/2PSsBgLRrGZmpphwmJiQ9Nk0izQLDSllFlhJTWSrxQxDSkWNopIo2wUmprFlKLExEKJDcViUrIQkY988//Pc+447+Ne6u28uun+6tc593lO5z3vOee95wA1atT4L5hNn9PN9BO9k00n5SsdpKfpUZfLxQH6g46FciibTor6X0zf0TUul4sHsE4baZvLpaSJvqJ1dL7L5aIXNvAbPlEAx+khH8zDTPoeNvCS3+muuFEi1G/8HPkt0yIHrfQqrLO9dCHspVKzgLbT13RVqCfZnpqVL7TBJxKzFjZJSVGH932wAPahoMEP+2ABXERBgx/wwQJ4hMSDr4ft+Vku3kKn07mwB2q/6mTsidroTJignVGsEitg/dx18WOwj7n0Usui+l9ZBJsRz55Q6t9HnenhOs5nTLUAVofctShWia2wtqdcvJlup2/D7x30w6/0n9lIz/pgxBb60QcDWq2X9JlPlOEMbPD9PkFu0wuhfoXeinJl0XJpFm/i9y0jNoXyKT0S6pp5Tzcd8cGAzgudptvoZzqeTU+yEvZSWgH976vel2nh6II1Wo7KS/QY1rH2+U66IZSeS3S9Dwb2w57zJpRaZc8SWE77/lyoz8u0cKyjo7B9+MLlSuym52EvcI8ehF2mPFrycnFxAjYYndzaCtOy6SkOwz7kh/SJy1U1WllNlNBdZ2mUq3p01+mgc5DotvkvOUkv0+s+UaNa+AmhAnXu3v4KAwAAAABJRU5ErkJggg==>

[image15]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAC0AAAAZCAYAAACl8achAAABp0lEQVR4Xu2VPShGURjHHx8lBptBbKwGpSTLWxSDwcKCSWJSlAwUhSzIokSZRIrF16YQgxLCqhgM8hEWk4//4zmXc5/el+597xvD+dWve87znPfce+77nHOJHA6Hw+FIMemwCT7Be7jrT0fGMryDD7BF5QJxCN9glekPwneY6Q2IgFmSOT1ipl9pxQLBP562+nVwx+onSyPJPc6tWDEctfqBKCKZsFQnIuSC5B5dOhGWObikgxHDD3yjg8kwBYd1UNEJT2A9nIQz/vSv8EPv6SDIhxkwD56SzM/wgbBt2nFJg8/0vQljcAUemz7XOp8s7fAFZsFek/OoJXmwLRX3GCDJd5PcrwSOwxqYAyfgLew34x9hn2knZAxekRx16yQr5TdgM0+JV58LD+C1Tlh0wDOSMtmHPf7056J4c3rtaisXmks4pIMKXnhY7JPlleRFhKKAZNVc0zxRmYlXfI3w06ADAVgwVy4d+/gNDNffIlyFbfCIpN7jwSXF48PCH7gNuAabVS5ljOhAALKtdivJP/zv2TRXLsOfNvO/opzk1OJSLFQ5x5/wAeSvTqRI73JQAAAAAElFTkSuQmCC>

[image16]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABEAAAAXCAYAAADtNKTnAAAA/UlEQVR4XmNgGAV0AZxArA3Ef4H4PxQnoqhgYLAG4tVA/AeIzYBYCFUaAS4D8TkGiCGn0ORAIA+IN6ILooNJQJzMgHANOlgGxIXogsiADYhFoOxeBoghgghpBjkg/gDETEhiGMAKia0MxP+AuAhJLAaItyDxsYIKNP52IL4FxIxQ/iwgLkVIYwcgTcjAhwHiJTco/zYQmyKkMYExEN9EF2SAGAKKUlkGTEswAMjvc9AFgeA7A8SgFgZM72IAUNzHoQsCwQIGiCEvgNgSVQoVgLzyHF0QCYASHbY0AwcqDBBFn4A4AE0OBuIZ8BiiwYBImbhSKAhwMEC8MwroBQBeZzGSthM0KwAAAABJRU5ErkJggg==>

[image17]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABkAAAAWCAYAAAA1vze2AAABkElEQVR4Xu2UTStFURSGX0o+QqJkhojMhCIDpCRDMTAwVIqJMFD8ARmZKCZkgBBCEZmYGJHM/AGRj6GQ8K67zr53nd09ugMz96mne9Za+5x17v44QJp/Tzldpc/0hg6EyzFy/QTp9uI9Wkfz6BHNscUXek5r6Bj9plN2AHmlh3QGOuYEOs5SYK7lBSZcUEzfaWm8DOzSTxML8kDf49CIMNl0zQVX9CBRi9EDfUiGyb2Z6yimkbhnh1a4wiPddkFAO7RJtcml0mSUntF9Wm8LT9Culk5oky6TkyYt0CmSDbJBq0z9V2bphZebgzYZNDlZowYTuxfJMrlIyqA7Jz+IM+kt9AG9bhBpNNeCLOwX7fPykXzQTVpC5+kWtEmzHZQEmbYFP5kqQwifAfmXD7TV5ARpsuLlkiLTMxn8OhYRbtIUxLJWDjddIyYXSRv0AbKQQhH0C3AZHwEU0lNaaXId0PtkfErc03W6TK9pbbgcY4neQbeuTJ2cr5QXXZCDIwdpHOFT7iMfv2Haj8RuTPN3/AAjqVEIrF24OQAAAABJRU5ErkJggg==>

[image18]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACMAAAAWCAYAAABKbiVHAAABSUlEQVR4Xu2VvUoDQRSFr0GFWChWWtuopWAZC32D+AJpgxbaWghR1OewEAIWgiFCirRJE0gbsLHUwlLwp9FznUy4c8ishg0pwn7wwcw9y+aQ2WxEMjKmkAIPhnDEgwTWYd3sF+EezMMtuGGyX1bFXVCFlTAasCDuxsfwmzJLC17AMryBX/DR5OdmrehnBujNn+CzxMvoNZ+w21/H0Mzag2smvzVr5Y72A/TrrPCQ2JbkMponsSnuiJQZuG+ygEmUURrwvm+UcZQpwmv4AptwJ0hHYBxlDs16SdwD/GZm/0bLnPGQ8GX0vIfB878e+Chahn96jC+T4yDCg6Qoo++IJHyZWQ7EPSsHNEtV5pKHhC8zxwF4h22apTqmKx4Svsw8B6ADd81+WdyLcqQy/m3JWjiLXfcKa+KO7AOeBumEWYEleCLuPy9jevgBCblUk6gdpqMAAAAASUVORK5CYII=>

[image19]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACMAAAAWCAYAAABKbiVHAAABrUlEQVR4Xu2VzytEURTHj6UUUWLLxq8FykZYICsbbCxlg7AWCxpC8S+wmKJoFoooC2HDRomFlI0lCxuSXwt8j3PfOPeY18w0VtN86lPvfO/t3dO7775HlCNHFtJqA0ceHIIX8BGuwlJvRmKq4K6qC2EHzIeNsFqN/VBOMmEDRvyhOJvwHQ7COngNb+hvQydwHo7AdfhBMi9gTl0zvKbHF7yFdxTeDM9ZVnWLy9ZUxnCm5aYr1XhMXTNbpo7DjzNiQ9BDcuN6k1+5XNNkaksNyRYxvPV9aswjrJkxkkXt/p65XJOsGWYfbjtDCWtmnGTRWpOfu1zTC6PwHh7ANm80DcKaKSFZtFNlZfDT5Rp+igFFJC/ws8pShpuZtaGDF51R9bDLbDP8HmgSPb2U4Gbs0Qs4gk+wCzaTHGH+5iRbaI+Sz0kIN8PfiFR5IH+hKBxVNZNRMws2dCzBBlVXkCxyqbJXeKpqJqNtWrShg294qGqex1m3yviot6u6mOSrnVYzwYto1fBRPYYr8AVOeqO/8NbtkGzZG5z2Rv+JAtgPJ0iOdRg8NgCnSP55ObKHb0/4afq70qIPAAAAAElFTkSuQmCC>

[image20]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEIAAAAXCAYAAAC/F5msAAAC9klEQVR4Xu2WWehNURSHV8aQyBhClCFD8SBDePFgKJIhEYonQ3kzU0S88IDMMoU8UJQHZSyJiIwpZCqFUhTJ7Pe7a2133+X+77nDuZ7uV1/37LXOuXufdfbZZ4vUqFGjRo2S2AdvwxdwUm4qVVrCe/A1/OJyaTIcXoVvRe+raCbAZfA37ORyadIMHhLt54nLpUk3OEu0n70ul8go0QurzTrRfvb4RBVgPzN8MIkb8n8K8V20n/Y+kTLj4CMfTILv7g/4yyeqAIvw0AerwGa43QeTmCg6wPvWbgrXw1dwUDgpJdjPNjvuAo+KLmp8GGlyB06O2pfhe7g/iv0DB8YBbhWdshfgfPhMEi4sA/YTvkxX4Bi4Gs7+e0bltBGd3a2tPU/0S3JACrz+HUSTvHAk7BzlDov+aaAPPB61S2W66JOaIjoTSDt4EtazdhN4S3SWnLZYqewWvacNcInFhsEzcKa1O4qOgX1lYIIXcRH7KDqQfDwQ/aM6K1oE3K98Fp1pQ10uED53nJncc3DApfJUdJwcbw+XC1yHC0WXgQyc+ryIT2UXfCe571YMZ0clhWABNsFTojOQMyyGg+KiHeD+Zk3ULgauOxwjN2w37djPrIbwJ3wZB3niJ0sSFoIxVnItXGpxUkkh5krutSwCd5iBwfbbIopx1oSFtVj4OrOfFdZeYG3SHL6x48CccMCTzkYJviLfYAP4GPaKcoUK0RveFd3V5SPsKANcvC7ZcVfJrhExO2A/F5sqejONXTzAp8x+hlh7lbUJd5vH7JiMEF0OMvCkxdlcZvFgIfhkwoIWKFSI0OFOnzCeS+61beE12AieiOKBAfCrD4Lzov8zzScM5nhz9a093mLsj/uXvhYPtHLtoihUCMI9BwdaKecke6Nj40QEC18uA+FFONoniiWpEIvgRh8sA35eA1zA81H2TYDlovexxSeKJakQnHr9fbBEVsKD5hHJfW0D3SW7uJcD150Poq9fvDinAgdW1x4kTXqK7kRrpM0fdVqkJhHsRSUAAAAASUVORK5CYII=>

[image21]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFsAAAAXCAYAAABkrDOOAAADkklEQVR4Xu2YWahNURjHP/MsU8YX5AEP5owJSV6MyZBEypRMeROlDJGpKKTIRRlKpqRQCCVDQoYiU4ZCCAkZ///7rXXOOuvue+7e++xDav/q193rW3udte931nS2SEpKSkpKSkpedsDr8AkckVuVKA3gLfgCfvHqkmQOvAzfw/VeXZLEyttIuAj+hs28uiSpC3eL9nPXq0uS3nCqaD/jvLokiZ23waKNis1y0X62+BUJU1tiJCEGsfJ2TWI0isEP+As29isSZh3c5AeLQOS8NYI/jcWGD3bDDxYB9jHKDyZMrLyNEU0CF3tSB66GT2E3e1NCsJ8N5roN3A9fw3qZOwqniejsaejEuEe8EV3LkyJW3jaLNuLO3QKehTPgM7jVuY9U8spRYT/DzfUFOBSugOMzdxTOWMlO7Wqim/IQ0RPKPXtTAkTJWwY24FQYAFuaGJO6XbKj4w48LxHXJ4+J8Kr5W2Ji3MAOiPZXC54y8V7wE6xsylG4L/qch2F/E5sOD8LOsCl8CbvCHuZervFRCZO3MrDRd/hBdBcvjwlSWLL5EJ/hA9jPqyMc5e76t1GyyQpLK9FnpMsk+DRiTxA8J/PL5JITZ8SHzRsHUQY24re+TXRd41oURKHJfgTXwqOi/2DH3GoZZOIWjsZ5TjkMk0Wf8SZ8Dr+JLlMuXFr4ue1ha9H797o3hCRs3tbYC25SH2FVU34n+iGMr4QLTJwUkmz7I8PSSXQjsXRxrglHHDc1JiYK/Ez209OUD5ky4cxh2cJfmkxS0CyriLB5OwHrm+vSJBy3BdGR9RVWgQ9hW6cuX7I5SnjcYmdB7JLctgPhaXPdTspuvHNFf277cG195Qcd2AenNZ+fnDMxsgdOMdeWPqKjf5oXPyO60Q3z4pawebOHgVJ2woVOmdOPjXgUY51LvmQvEa3jDh3EY8lt2xxehDXgESdOONK4gXX34vxCuEbyc9g+CNYdc8pc9xnrK7rJV3fqLDylMOEubEPZJogweeuQrY5OvmQTvpOwozUufFnFWWIpbx2MM/UtJ0X/j9GmzBNS0P/FL5ez5J9QUbLnw1V+MAKcgjz6lRi5aXFt9+E6yZdacZkJb4uupTz68RXCvpw7FB4TL/nBv8EV+FY02Zx2PDn4cMr5J4wo8Pxtp6816Eg1yQ/EYLboiOaRb7EEb8Q8qs7ygzFI/B0NH7amHywC/HWYs+kUiaWiG3fK/8Yf04voP3LVI4AAAAAASUVORK5CYII=>

[image22]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAHUAAAAWCAYAAAD+ZNNIAAADvElEQVR4Xu2YWcjMURjGX7Lv2xW5sJQt2wVSZC2UC7lQLmTJFVmy5YLkkyThhijKGkpE3NuSkiVFsmXLhexZUtb3+c55zDvv/Ge++WbmSudXT/3nPed/nnnPPiOSSCQSiUQikUgkEolEIpFIVMpq1W9Vnaqt6oLqu2qArVQj6NNCcj5/8mrUBuREH+REn1rm1Ep1UvVF1UTVR/VK9dpWqhH0mSk5nx95NRxI9pD5PDbG8EVryTLJ9nlnYpZK/eHjJwp9Km0zi9MS2p1vYutjvNZk+fgc/3FAwoqxbJfCFz6rhsdndM4oU1YO8PFt0me5iU1WnY/xVSZeLvTxOXmfuaotquaqo6qfpqwcmkpoc4OL31QNM5+nqh6oOquWSngHq61c4PNYsn18f9aDWftBwsy23JLCFy6bZ8zExsxG+vg26cPJQrrFeCWDSh+fk/e5pnoRn7tIA1tZBmgLbQ41MQzcLwkDQTZJqIdVNiY+7zPlDVHKB7kW0FvCC3bVIUG88NHEwAnzvFuKNFgE+vhBpY/tBFDNoNLH5+R9LkrYfchz81wOCySccbbNGVKYY3fVClUH1RwJ5YvyapQGPngny+ecif0DKwiHOrYgwmW9UXVMwgzrqNpv6myOdXBgE1waXqqmmxihDwaRtJOcD7DnRalB7a96qOrlCyL0YU7wQU70QU6eWVI4GPS54+JkkOqK+TxQwsThAGAXwGQme1T3VD1MjNAnKyf4+O9GnwmS77OLFVaqFsZnLPGrEl6okzB726g6ScODyq3lvolZ4MMvB5/r8TN8+knwIaUGdZ2EMnRSFvRBTvRBTvTxKxKD/lTCWWyhj+9QC27U6HSAcw8Dg/rzJHsV4Ux/rxrt4vQplhPaog9WKX0mxjKyzTzXJ4rtFB2AGY4EP6nGxfJmMUa2SmgUnU9aS5hBSBT1s0CH02eK5Hz8ROCg4meJBz9Jnkj+Ge+BD3KiD3KiD3MipySccf4IoM9bF7fslVCOgeqr6qm6JGEFZ63IlhJ2kUcuTp9iObWXnM9ZyfmgL+mDndIujLLAxYJgdmRdlIZIfr1K4aCu8QUG3FyrxW75xcCNtRowyTGQXSV0PH6nv8mrEYBPLXJqFN9UI+PzV9UIU0Yw4xf7YAVwUNf6ggh2gsE+2EjGS5j5B1WHVWdsYQQ+OAer4bjqiIR7xRIJefk+ok+1OTWaSRK2FSz/aa6M3JXwD041YLU/k5A8Jk/Wat3hAxWAywnPMsoDH3uXqARsiTtVt1U3VLPzi+uphU/if+UvOzsHlLA5FuYAAAAASUVORK5CYII=>

[image23]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACkAAAAXCAYAAACWEGYrAAAB40lEQVR4Xu2VSytFURTHV0ReeZTCxAilTAwkA+UTGCB5hFsMfAMZKJkYkAwYSElmRJjIhJkQmTDwSHmWUhTKxOu/rL3v3mff69R1YnR+9Yvz3+ucs87e+5xLFBISEhIS8p9kwSe4C8vhBLxRWb5VF5RGkuveq+N6uA2PYIsu+gluipv7hIewF6bCInWcYkoDcQkL4Txcg5uwDA6Q3LvNlHppgoskBVy44R3+zkbV/5mwE16Z4YSoUH9PYa2Vl5Lch2W64Q7cI5ntKFMkRf12qDLd5D7JzL6Z4YTh1eFr2qvD20A3GYEjMAnOwA9TRnRCUlRlZXkqi1jZOAVrspXMjGnGVHZBskevYQ7Mhq+mTIqW7QCskDyVTdAmjym2ST5+gQUk70Kuynk2H3URw4U8vZpq+A7TrYzxa7IB3lHsORq91G6TvKTNTsbwfvTU6qepgzXwFm7ZBQq/JtdJrtPlDij0y8nn84NkkHxZeuwiC96CC/qgHa6aMV+4SZ5hP4bdQHFG0mSlOxCHIZLljjIN++zAB27S88bFgZc9HtzgM0x2Bxw64KQbnpP3u+UHN+nuKZtimOaGCj7P/Q67cB8PcBbOwSUO9UZmD3TlLymBg25I8gtm38fvIePiWfc/gpf31z+tX0i4cYVHMbuTAAAAAElFTkSuQmCC>

[image24]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACcAAAAaCAYAAAA0R0VGAAABz0lEQVR4Xu2VyytFURTGV17FAAMDRBkQhT+A4o+QJDIwMJAihTBggjEjpQwojzFD1FUSRoqBN3kbEEqe4Vutda59930Wundwvvp19/722rvv7r3POUSuXLmKWHngS8n1HYoNcbBD24wVcbhx24wFJZCEy7EHoqE0MADuwTKoAfs+FVFSMTgBmyAODIEPMGbURE18fINGn4/0EWRpvwI8k9QdkfyJK+DR8XCaB5ck83fBDjjQ/qRR56cSkqJSwytTz9SwerzLrHjQApq9FaGVSf5rdoIVy/NRHzi2vF7yX8gJV2j5b6DA8gIpUDhWyHBTYMbyFsh/ISdcvuV/glnLCyQ7XJ3+dpPc84BqB11Gv4dkkW1QD6bVDxZuTX3eUX7C90AGyX3le1aldU44vm932g6rdLABkkEKWAevYEv9cq0LFm5Vfb67/JD0G2M851Tb5s4lgglth9Uiyb+5IJnYAM5Bh1ETLBzv1BNIIhlvNMbMu2sfa63R/rWccPblf6efJ/2B5EXuaJTkaFl2uD/VCMniRdrnHW4Crd4KojaSr0oqSZgbklNgZdM/hasELySLn5Fc6luwZBap+Fg9JJ/AavXmwDXJfH4Jc9+VK1eR6hte0nS5mxadiAAAAABJRU5ErkJggg==>

[image25]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAmwAAABBCAYAAABsOPjkAAADoklEQVR4Xu3dS8inUxwH8EPYoInkMmFcVorIQjHDgo3ESjZKLETZWEmKbNRoalITNqgpKxuXKPdLKNcaSmGaRhZKKLckd7+fc/7ve97z/v/zzmLG+9R8PvXtPL/f89R/ezrP/5ynFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADW30ttfH1FFwCAyfi7jf+s6AIA8J+fIhdEvoq8Ntw7t9RJVD+R2tzqi7veh5Fdkcsil0Y+iHzf7p1c6vP3RU5qvTNb77xWz3wx1AAAh7ynIu92dU6irujqDS3Zv7PrX95dL1oVe7uNh5X5z9w01B9FNg49AIBDXq6GvdjVObGarYKl7W28rt1LN7Qx5arcx13du7CNt0f+6m+Ea4f6+cjOyJ6hDwBA567I10Pvt+56NmHrX1tm7/Sunidfjd4/9D4bagAA1nBiqatlo63d9WOR48rqFbl57umu85mjuzrl608AAPbT4ZFPuvrsNh4fOabrp72Ri7p63oTtyLLylee8ZzaNDQAAFvsmsqXUHZ43R45q/YeXnlg2Tr6eLHVH6MyxkWe7OuX/17I/82p3DQDAGvLA2pyE9UljPZNHgIyujPweeS9y2nBv5rlSn9k59AEAJif///XI2AQAYDr+iJwyNgEAmI7xFeOB9Hipx3DMNg0AALCfno5cHzm/rD5A9kC5sdTdmSl3aOanomZe6K4BABjkrsvdXb2tjV+W+no0j9MYD6vt5aGz+Uf/PGj2l8iOlbeX3DE2Sv2D/xtl9dEcAAB08hVoflg9nVCWD5A9IvJyu06LDpK9OnJ3V7/ZXY/yXv5e/y1QAADW0P9nLVfL8pDas0qdsPWvKmfPPVDqOWjnRDaXOmH7NvJjqWelLfLEUN8S+TPyc+Sh4R4AAJ08MPa7yDOlnlH2VusvmrD1E7y87lfY9jVhm5JrSv2A/L5e9QIATN44YdvTxn7CtqvUCdu9XW+qclK6KbIh8k7rHcwdsQAAB92iTQe50zP/i/ZKq3+I/Bp5cOmJ6fm01ONEcnLZyy8bAAAwAfNW0j4fGwAA/P9uK8vfG+3Pl3u0jWd0PQAA1sklkb1dfWpZ/OF4AADWwfuRq8YmAADTYRUNAGDiTNgAACYsv9qQ3zcFAGCCcmXt1lI3HQAAMEG7IzvGJgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEzDvyy+nRc6xL8gAAAAAElFTkSuQmCC>

[image26]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAaCAYAAAC+aNwHAAAA3ElEQVR4Xu2SMctBYRiGH8lmNhkoGVi+wShWxT/wC5Q/YLDo8ysMBpuY7FI2We2KRYlJGOS7H88Xp/u8dBbbuepa7vs5z1vveUVCvsYM3uEKlmEWluAcVuDpOemgCY+wDiPUjcUWq066YmWGi39+xHo9wMdVrNQln9jDBoeKfnyGCS6IBUxzmBdb0OMiKCOxBUkugjKFOw4dtMX/Zx4M4ZpDB/oOnLTELjDGhQftqhx60TvYwBzlcTiAE8p9/MIbvMCa2PMtwi3swOhr9D0F2Bd7VAe4hCnvQEiIiz8PnCmQ82T68QAAAABJRU5ErkJggg==>

[image27]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA4AAAAYCAYAAADKx8xXAAAAx0lEQVR4Xu2SsQpBYRiGv8FmopTY3ITJqJRBKbOSG3ABNsmoZDa4D5tsCoNNJuUCLCLet/+j03tOmWznqWd5Xl+dA7OUn1ThS3zCsu/DhP1LIykKcw1kbOHookOEvQaysXC41MHJW3j8GHcLhz0dnBY8aiQ8OmuMsIUdjYSHC41ODj5gQYeshcOuDg4f86CR1C0cVnRwpnCmkUzgSmOEE8xoJH241ugUYVPjB778DZak8y+3kxaDvyO/gDaswRG8wkH0Qyn/5A0fCiumBfZY/AAAAABJRU5ErkJggg==>

[image28]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAwAAAAaCAYAAACD+r1hAAAAs0lEQVR4XmNgGAUoQAiInwNxMhD/BOITqNKYoA6I/wPxdijdgiqNCS4xQBTyArEqmhwG8GGAKD6ILoEOOIH4KwNEMQz/A+JSZEXoQAWIdzFAFFcAsToDxCC8AGTqbyBmR5fABUCmX0QXxAdAGhagC+IDIA356IK4ADMDxA986BK4gBYQ30AXxAeigXgOuiA20A3EHEB8mIEI59gyQDxqAcTf0OSwggAg3gzEWUD8Gk1uFAAAobEi4ke/bnAAAAAASUVORK5CYII=>

[image29]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACsAAAAXCAYAAACS5bYWAAACGElEQVR4Xu2WT0gWQRjG3woqKvIURIpgKAUR9AdFUUEv4VFQlDDKQ/fwEEFJSAThVa1DFxHsEl6sSwc7edDwEhGBiWAEiRokQhdL7Xl5d3X2ccYdQk3IH/zwm+ednW92nZ35RPbZ5/+miYPdpALOw4+wimrMA/iMsifwC1yG/bAsW45Gx+jk0OUc/Anvwd/wTba8ic+w0mkfF7tGb7IOromNd83pE4te28Why6BYpw/J37vZcoZqOElZDzzqtIfFxvnhZDHUSs5k9WloB31aMegEip32VbHrrzvZIbHloHksj+ELyZlsh1iHAS4EeEvty2LX89JZSvIYLsJZeEoCk70EV8SKqauw3enj4ya1D8CXsNHJSmRjzBjG4a3ks3eyh+FZOCXWoQWWJnmIQrGXKY+HYmP+4kKAEeezd7IpWpzmMMAnDjzok9Yxe7kQQF9Gl9zJDnHoQffhGQ49dMFuDgM0w/eU5U5WN/k8nsJHHBJtYus+hgL4FZZTHpxs+i87zQVCj9ZRDokF2fzy3aG2i6798x51Pn1Ov3X0SPzGoYdX8DaHDnqz+gU1iXWwAb5z+ihz8D5lTPDJtsLXHHrQPfMkhwnH4IRsbFVsih4U2vadagfhCXhGrM/zbNnQLeMKhx7+5ozfFo6InVq6Xhep5uOC2J3/E9JfVukxmUfsNrQjFMHvYpuxnkhbUQ/HONyr6I/gGxzuBn8ANyR4XtEZjR0AAAAASUVORK5CYII=>

[image30]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACsAAAAXCAYAAACS5bYWAAACUElEQVR4Xu2WS6hNURzG/yhEeczoirwykPIoXZfBUZKhKBLJwBQZSB7ddOsmmV2PISkjSWFCYWLgNUMKeU3Io8greX+f/17XWt9e+5xdclLur36d1vdfe51z9l6PbTbAAP83KzVoJ/PhC3gbLpCasgselmwvfAI/w6NwelpuyjH4DL6Dm+CwtJwyA36A2+FXeC4tl7gHO6P2SPNr+Ccb8If5eEujPlXMhN1wKhwOH8LzSQ/huPkX3Cw+t6XlhIXwrmR95l8UOG0+zusoq+KqtPmjP0nWD+8GB+bdqgN/wMSoPc/8+jVRNsR8OjBvBp9Ors91DQJbzS/gvKnDRWnPMb9ep87bIm/GePM+fLJji2wW/Nbfo2B2EbJz8DvcEPXJsV7ag+AJuDzKJtvvMVtxyrwfF9gK+AgeSnqAoXAKvG/eeRWcVuRVdJgvplZwwXDML1rIMNrSG9abllPY4YGGFdzRIAPvNMc8oIUKlsD9sAveMr+2NA0CLJ7UMAP34ccaZtgD92lYAbfM91GbT5VbZ+X0YYGbfCs4j3o0FNaaz/u6cGFxIcbwDmv2i/DIxmlB4NF6WUPhpZUX3xZpK1wvlzQ038tL8Eh8qmGGM3CjhhH8swfhosIGXAavRX3Ic7gzah+BH6N2gNtpidXwrIYZ+FhGaVgwAt6wdEXHBnhQsB2fapPgK0sPmYb5O0KJC3CuhhnqnPF/QgNuhjvgmLjANxreZs7XN3GhAr5oDNawXYQ3q3BMtqLuNvRXmGA+T/hmxBOpGYvhFQ3/VXbDdRq2g59bsIG41TcLCQAAAABJRU5ErkJggg==>

[image31]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAF8AAAAWCAYAAACmG0BRAAACs0lEQVR4Xu2Yy8uNURTGl/t9RsrApRQDpEz9AS4Tt0yVCQmJIhJH0WcqjNwTkUsuKWGqDCS3YmZggIFLitx5Hmuvznq3dc75ysB5nf2rp2+vddb71Fl7v3vv84kUCoVCoVD4Z4yBnkHbs/wAaBV0H3oJnYAm+4LEFOgU9Aa6B62sfvwb83otTa8COAj9hBpZ/hD0EVoOjYOuQW8rFSIzoHfQdWggtBT6UKlQzIs15jWrUtGj/JC4+cxtc/Fo0ZXLBhpc6czx7TG2ik6CsUhirwdS9eo5dkNn5M/mj0+5ES5H+qD9LmbNXheTYaITOjbFNrm5F3Peq6eYCb2QuPnzoc8uNriq77iYzzGXw/w8N468mPdeEetEt6xWb8gg6Eie7Hb4ZfjFV0jc/DXQexcbG0UPTIPPMZfD/Go3jryY914Rw6Eb0EnRRnsYn4YuZfmu5xU0NY2j5u8SPUhz1orWDhG9wXC8oVKhML/HjSMv5s2rE9yybkKDU8y/F6V/z3YdW9w4av4OiRvGbYC1bDxp13xOoI0jL2u+eXWCb8EFaCR0Xmra+GXSXEEkav4mibcKNppXRoPPtdp2Nrtx5MW89+oPvNLyrb2cf1AHForePj45fRdtxDfodqqbnXJDU2zwtnPVxayx7cXgM8zPSbGt8NyLOe/VCb/ya7nljIKmZ3oi2ogD0KRUxwOZuYkpNo6JvhUGa466mNCD24wdkPzlG3kx573awT2fB6/f87n68wmtHfz3ARvRyPLMLc5yD6EJLuYVkj+WPEtEJ9LYJ7HXF6l6tYKNvwWdzfLnoCtS0wmYK80twXTXfc5t4zn0GDos2mhuOx6ubjb6K7QTegQ9rVQo5tWQpld+dYxYL1rf7p5/PE/+L3BVccXyzm5bUsQ00QN2gVQPcw+9WNPJq1AoFAp/zy/7ibN7Fmcb0QAAAABJRU5ErkJggg==>

[image32]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADQAAAAZCAYAAAB+Sg0DAAACSElEQVR4Xu2WzUsVURiH37LS8mMnmAm2EVxkQitRUbCFkBBCIhG6MUpdpeEiEVwIEbpQwVUtCg0Mijb9CUGJCImLBKUWBlGUZNIHWor9frwz9M65d+6t6+YK54GHO+edc8+c93zNiHg8Hk8Mn+EdeA4uwj24Eqkh8gnOwduwG07D7UiNLOEQvGfKRfCDaFKWb0HM+iZSI0tohOVO7JZoh8+a2Ff4Hv6E8/AmzDP3s4Z+0c73mVhdELtuYuuwxpSzlhLRfXPaxHpFE6o1MSbUBu+LztZz2GTup2IYrsId+AregIfhM/gWbsCj8Jro7H+BT2AxHISvRff5KDwmGfBCEvcQG/wBe2A+fAh3IzWSwwH7Djvhcbgm2vZVeBlOBmW2Ny7a9kgQY8JDMFd0ABgbk//kHfwFLzpxLjc2ankJp5yYpVm0E3avcV+2i85ICBNuNWUmFR48FpbZt3+GD+Gmv+DeiOEpXHaDhglJ7FQyeIJWmzIHIC6h304sJQ9gvRtMwazoeo/jkSR2Khmb8Iwpc5/sK6EO+BFWOXG77NjYgikT7rXHTszSIvq/k078RHAvxE2IKyUuIR4saeEa5hHN2WmA5+ElWGHqcGlxT4RwnfOQaDQxF760OQhcepYBOGPKfL4dzFQzlPYgqpS/f3bNMfWW4Kngmh29K4kPTEaZaD1+WvHEuyL6WcU4B4XP3xI98fiVwrZ5cIR9KBSlwMTsC39f8L3A47cLljr3MoGdPCKaBAePCfIk5TVjYR1e85eEdT0ej8dzsPkDbMeHRiatY2wAAAAASUVORK5CYII=>

[image33]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADQAAAAZCAYAAAB+Sg0DAAACTUlEQVR4Xu2Wz4uOURTHv4xhMFgJNTIbmeRXfiRGM2ExZUpKSWIhkVmhLEgkG7HA2iwUCws7fwELCylWs6AsZjajFIk0fvt+O/dy3vO+zxgzi5e63/r0vuf73Od57rn3nnsfoKioqKhCr8llsp48Iz/I85oWwBHynVwkbeQK+eob/CuaRm66eD4ZhSXlNUbuB+8BWRS8pquXLAveGVhCa5yn+LCLpVPkfPCaLnVKnT3pvO7kHUvxvBRv+tXCtIN8IjOC31QthtVNp/MGYAlsTfHqFPsZk7Ylf2nwoy6QF7Cae0pOkOmwJfySvCWt5Ch5TN6Qe2QhOUuGYHWuup2JSegRamsod3yV8yQlLH9d8L00YB/IITKbDMPu0Sazn9xI8R1yjcwll5KnhM+RWbABkHcVf6kR8pnsdp6WVqOEtiQ/LsWsPth17YpZmuV9sBnJUsJ7XKykdJ8fVEmx+jZh6SUfya7gb0bjJZdrbWXws66jvlON9J6sdbEGoCqhL8EbV7dgyyuqA/awjcHfnvwFwc+6i/pONdI71M6+6mRKCR0kr2DF7+WXnR6mdl7HYZ2uUj/sviXBn5OuZcWEtFKqEprQYa41rC1as9NDdpK9ZLlro4epaL0GYXVSJR3aT2BLz+s0ue1ivd8P5ngz9C14derC75sjLa7dQ9h22pniFbC1/yfl5apPK+14B2CfVfJV/Hq/vkK04+krRYOgWs190BkotTsv1vKU1As7hDfEC5OQOqlDWUlo8JSgtmf9l5fb6L9+pdy2qKioqOj/1k8bEIO+Y3Df5wAAAABJRU5ErkJggg==>

[image34]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAB0AAAAZCAYAAADNAiUZAAABMUlEQVR4Xu2ULUsFQRSGjyiCX8EgfgWTXfAnCEaxGAWxWLxis/gBNhXEYjOKCIJgUjBpsNttiogYxGjR5ziz3JnDzkV0t80DD/eed4d9dy6zVySTqZghnMJTXDfXCo7xA2ewDe/wEUeDNUs4iP24GuSlfOEDvki6VNc0gnkYP/HCzz143rz8w4SZIwb855W0Lg13pdz6XJnEteCasmjmUlKls/huQziUZqlyFHwfx45gTpIqXcFXG8K+xKXdeIlnEj9AS1KlG/hsQ9iVuPRPpEq38cmGsCMVlequLHpAyna6JzWWzuObDeFAKirdtKG4U6g3L16tgmuf/wst3bKhR28+Hczt4k502S/wK/pwDO/xBEewN1rh3tMb7PTzsrgHWSgW1EUXzok7WPp/nclk6uUbVjA8ntTID+0AAAAASUVORK5CYII=>

[image35]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAB0AAAAZCAYAAADNAiUZAAABK0lEQVR4Xu2UTysFURiHf0n5XyxckrKQnYViIUuylW+gbFhasfGnfAVbpSykxEqRb2Fjw0ZZsJOFEuI5nbk5521mbhhW56mnOe973nt/08y5V0okKqYfZ/AQ181enSc8xlVcwAv8wJ1gZgn7sAdXgn4u7sM3eK/iUDdjdTfRmu134Em2rjNm6oje7Hqu4tA3vMUXfMC5eFvjuGZ6i6bOpSz00TZy2A3WI9gc1IU0Cp2Sf5duvYeD0YTUjmd4pPgGSikLfZd/vNPYhNfyZ2A4HPoJZaETpq7p60D9Che6YZsluMP176HPqih00zZhUv7Lt4Oe+5lV9ni3bBO68VTxaZ2XD7wLet+iC4fwEg9wADujCWkfW4L6Cl9xNuj9CaO4LP/P02b2EolE9XwCpm8/J970OywAAAAASUVORK5CYII=>

[image36]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAB0AAAAZCAYAAADNAiUZAAABTklEQVR4Xu2UzyuFQRSG31B+XIoFSnY3ZWGhKLJUtrK2UVJkZcXGhn/BVilbP1ZKWc2/YGNjQ93EThZKiPc083XnO/eI0b27eeqpOWemOTPzzXxAJtNCTukXXVP5F3pGt+kKvYIfdxCNWafDdIBuRflfkYmsokU+VhbRFfor9Dy0CyZVbNJHH2AX/aD39I0+0cVyN6bojsqtqriBGXpHHeyizyq2OIzaY7QjihuQzmv41Tv8XHQO/ltK+4iOlkYAPfSSnqC8ABM5FrlAgoNd9BP+eOdpG72lj7QaD0phM2o72EWnVTyE+oVKZhl+5QUOdlELuVzJReU91VTO4e9FX/GPor10XCnfSSbapSNh3GzI7YdYGAy55KIWsnO90356gfJtXYIfp08qiXb4nctzkMn2UP/bCMe0M4pv6DtdiHItYYJuwD+xbtWXyWSazzeTv05YAB/aogAAAABJRU5ErkJggg==>

[image37]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAB0AAAAZCAYAAADNAiUZAAABS0lEQVR4Xu2UvyuFURjHv+T3TZGwWCR1B4NikFHJIpeyk4VMku7dldlgVaJMYhAp/4LJYrmTMrDJQEJ8n8659z3vc9/3vd5etvOpT53nxz3P2z2nA3g8f0g7/U6wyfa90FNapEv02tb3bF1Ypf20m244+RpGUDuo4rHTp2uifESbrefomV1XGFVxlQW6TBdpgc5aD2ln0IZPek/f6ROdc2rCGC2p3IqKq6yruJne0E2Vf1ZxFPvOehjB0dRlh17SBpWXoZMwZynrAzoQ6gA66BU9QfgD6vJGh3SSfMH8vVO0kZbpI6J7UzEDc75RjKu4D8GFysQ5zetkAnK5Mg3tgdmkRRcSeEXGobuI32ACprbt5HptLu43v0JuXdwGXfQC4ds6D9P/4ORSc4v4ocIRbXXiO/pBp51cagbplk4q5Mlcg3l55M32eDz/yw/MiUpb/403mQAAAABJRU5ErkJggg==>

[image38]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABsAAAAWCAYAAAAxSueLAAABXUlEQVR4Xu2UOUsDURSFLy5pbLQSEVJaCCKkFNxKMYWVWJjeRsEUWvgjBLER3AorxcIqjSD+AFELC6tEXBCxEsRCRM/1zQx3ziTjGyGVfvAV79zJnMz2RP75q4xxkIUJDlJoh32U9cJd+AKv4WpsCrrhCNyBmzRLY4rWg/AeLsFWOAc/Yb89SIPbwCxlR7Q+hQ8SvztnQZ5gT/zLynCfsitxf/zEZBX4ZtYRWcou4SRlPXAGdpqsCo/NOsK3rAAfYRsPiGFxVzrEA8W37BkOcGhYgR/wHZZoFuFbpg/9J/RtnBVXmKfZN1q2xWEd5jlIYU3c55BAy7Y5JBY5MOjv12GHycLnlsCn7IIDg55UtVdeDLIEWqa7SCN0h3ji0BCW2Y96OcgiwoNYi77m+rprYSNGYQ3ewA14B19hzhzjhd6Ocw7r0ALHxe2P07ArPvbjAC5w2CwOOWgmeht/zRe6SUsBRqMEwAAAAABJRU5ErkJggg==>

[image39]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACkAAAAWCAYAAABdTLWOAAACB0lEQVR4Xu2WP0hVURzHfxpmkbQkSVSTg4uDaA2iDi4OFoUgNDi0CCqooCBYiCD+g5YUFMSWltJCG8LFLWgTFEdBQUTBSgVRaSry+3s/3/Xn1/u89w2KhB/4wDnfc959v3vfOec+kSuu+D95wcFF8IyDCF5R/wF8D3/BZfgW5vkJZ/AIzsADOA9f+8G7sAyOw0k/EMEt+JCyTTgKS+A3+E+s4DiswTqYI3YN/WyAdjbgqqRX5EsOwLRrX4eLYtfPdnkYesMLsOCor/N/Hw8fMybxi8yHu5S1ij3JYpfpPC1yxGVh3BObN+iyH64dkE6RvfAdZc1iX9TnMl2PmunPF0UNvHbUvgP/urGAuEVmiq0fXceeXLgEC11WJVZkk8vi0Ca0JpPELfKD0M5LQRH8Iym+LAVfxdbiNiylsQRa5CcOQ9AjQo+aKJKbRp9KuvRLipvTIj9zGMIsByFkiD3FBh5Ig+8cKFrkFIeEHhE3OCQa4T5lT6jPVMBOylqon0CL9OdcGAMcEM/hjpxeT93UZ1bEft7HLuty7QAt8guHDt3V6xwS+gT1vCwXezqVsBrWujk98KecPBPnxNb6fZdNuHbiDsJkPsIODh264/kaSbPcvDdiBQ27TNkT22z6etZ23NdpwG2xD+qb4by4KbZc2uFTiX6VnqJe7B/KpWZL7A/DpWaIg4vgEDVCbLohxV1GAAAAAElFTkSuQmCC>

[image40]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADUAAAAWCAYAAABg3tToAAACeklEQVR4Xu2WS6hOURTHl/f1jsGlUFcZi0jKFJFHMTFSGBAl1yOPKBIiDJgwwBcTBh4DRh51MzJEpISiS5LIayCF//+uvT/r/M/JVZJvcP7162v9v3X22fvstdc5ZrVq1ar1FxoOzonXB6wD98Br0AATChktpsfgONgAjoI34Fshw+ws+ASWgLHgOnhbyGgx/RA+gqWFDPc3hXgE+GC+gy2p7WqIxpkvaoD43N1D4rWMelvUIvBFTWgvuKXmP1B/Nf5EexLPwEOw1opltR68C3HWLvBUzaQx4C54AT6DYeAAuA9egoOgHzgJnoD3YGXPla754AF4BfaBiebNi2M9AsvBFHAVPAddYBYvzLoSA+i2ebll7bfqpsAd/qqmaIb5WJuDtyx58R4UY+26W8F3MD14J8xzJwXvcvKaGhUD8ycaE1hmVYvaYdVlGcXJcKzRwVuQPL2WHrtq1BbzHY86bOUHwu6sXkEsNya0p3ibVZffTvP2/ztNs/LN5iWPZRRF74Z43GGtJJaujtmI3ipw/td/PcqL6khxftp6YI9Z+VoV614nMDt5PDNRVYvqBBfF4xnTMU9F71oKhjb/9jNELzcLLobx+GaG6wJYI55qqpUnMCd5VYu6Kd5GKy8qzy/qdPT4nmHdRnVZ+SLGi8Xjl4ieR1Xe5ai5yWOnjaKnrwjO7ZJ4euapwqIotkR2vIZ5p2ENj4wJ5pPrNm/JZ8y73u5CRlEd5jeJsHXPFO8OWFiRu6LCyyUW4fk6EuKmBpl/07F9To5/iJjHz6fV1vvHbF/zkua7iGIJ813F3+yxvJnDL5W24DHmvQjHoTcQDAkeRW9wInu1av0v/QQVFanBZrHEFwAAAABJRU5ErkJggg==>

[image41]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADoAAAAWCAYAAACR1Y9lAAACUElEQVR4Xu2WPWgVURCFJ/4g/pZqI0S0sFAUtUhEEQUxRkQLGyshlYUo2FiIENEmTSy0sNLWSm0EsbATjAgaf0CxSIqIqBEtBMXEn3PenXHnzbtZVgiywh44vN3vznlvZ9+9d1ekUaNGjWqsJfAYfDYOlGgLfBP+BN+G17UP11OX4F/wYOAz6Tj8Hb4g6SZdlXSjaq+f8neNsvaEHm/Vc7rWOg9fl+qNXoGHAtsN7wqsVtoAv5Xqjc6B38FH4sA/0oIIqogX/QA+KtUbtWnKf48z4RX8ED7kizIahd/A3+DFkrKPJd3kYXg+fBF+CU/CJ1OspRVS5B9Jkf8gRX6ZFHna51v/zFo9rtroMUl19x3jRb6XtDmVabOk7BnH+pXF9c3zu4GV5bk5mjjb2r7vtDuu2ijvFOva7hh0T3mZNkmqWenYTmVTjlFkTwMryy917ICylg7D84qxyo0OSKrbG/gt5WXaKJ0125VNBE72LDDmvwZmea/9xnjAxwnXi/mHDk7DIxrIabmkuh2B31BepvXSWdOjrEqjzH8OzPJefca4mPkW4/1cBy/D3al+RnFKHQzsjnT+YBR3+FjTqyzXKK/Ji/nYqOW99mXYH3E34+Bg4Pwx7nirHDsFn3Pn1Gsp+XKVrTGvbcpyjb4IjPkvgVneK9uozXHvJ258XFITqx2j+Gj4CF+TNN35CunXfFT8DTZmU9nMx0LuerozjPnIYn5WNBfeI2nnXhPGcuJyYYbiDeH7Mc+NdSnj2ELHeM7nveWNsXaRMsoYP401avQ/6jdL47dtQwNpYgAAAABJRU5ErkJggg==>

[image42]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACwAAAAWCAYAAAC7ZX7KAAAB6ElEQVR4Xu2WT0gVURTGT5p/INoJ/iHiSUki5KJNa3cGtnOZoJYILcTEIGnRIpNEcCm20GjrSnDjwsWDQmuvUEHaIjGMoGWCoN/35tzxzHHe44mbWcwHPx73d88M587cuTyRPHnyZCZ1YMbLLGUXLIBn4I2OTxIVGQubsxyB8URFxjLtRdZzmYYbvLhgGr2oJrPgOfimvAD1iYpkesFXcAgWQSt4B/6BPYmuZ5bAd/AXPFHHNIFtsC/Rfbjol+AA/AHL6l6BHfATzPHCkCK4YsYfpLqPbkyiOi4gZEKdv57jFee61b817p66eePuqovTbAfIY4kKrjnv8xT8cm5Eomt/O0/3ybku9beN61DXaVxBXdk8kKigx0+4jIKPzoXF+uboNp27o77WuFvqrhp3Q10pA2AN1MTTZw33GZcW7ssN5walfMNbzvHJHjtXkPMNt6grZVUHbfG0yLA6v1V8+Pp9w0NSvuHPzvH1+4bb5XzD/Kjjhl+DqbO5Ut6LKagQ7uGic5Ua/uJc2MP2g09rmA8z0c8PiW7GRrli7subtsDlkUQ3sKynOD79/hQf9qTlf4pjLzwCwzgOV/MQTIL7dqJMeEbzwOe+59PhnyWeKMEx9HShNjjWsoZz/Njo+HvdOCa4MJ8nj88pMN+CVUGzwSQAAAAASUVORK5CYII=>

[image43]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADoAAAAWCAYAAACR1Y9lAAACa0lEQVR4Xu2WuWsVURTGj7vGhWCjgga1cAEl4oILLoWNC/4BFoKFaKOmFYKF2GtppY2VVuKCYqGVICK4g2CTBMUVVBBXXL4vd47vm/Nu8h4Swgjzgx/J/d45M+++mTt3zGpqamoqxmZ4A36Ct+EBOLZUkSdXsxGeiWFV+Aj3wxXwFfwNr5Uq8iyFV+BRuA9ehr/gRS2qCnPhXhlzsj8tTbYVrGWdehN2alFVuARvwcmS9Vr60qsly7E8BlXmgqVJrZPscJGtkSzHshiMIpNi0IpN8KqVG09bmugMyXJwoqssrc338BxcVKpo5gF8Ab/CqfA4vAdfwhNwAjwJn8J3sCe1DTLLGv13rdH/1hr9/M7eT7W/xDFLk+TBWrEYrpcx/2dvn2Q5Vlqq4xJxdhRZfDZwfD1kw/UflGx3kWX5Bt9Ye+tvYhhzu+GVGvLgBf4Qmy3ZliL7IRlh9jBkw/VPl2xXkTUxBw5Y2jb+lX4b4uBCtzXXcP9l9jzkzB6FjP1fQub9ys6YjbP09L2vIZgXxso0eMfSGlfamSjXdqzhw7DdibL/Q8i8X9kWs1OWFvdMycbALhlHuPXwIHwAOLx1+UvHE0a4LGKNr+/cRB+HjP1xot6vbI8Z34Z4mXn5+Tq4FR6yNFmHJ+MTz68y18J3uPBvhdlaSwf+LFkOX2PKhiLLTfRJyNjP11XF+5XSRPmOy0FOpQ8+gwsk4y3/Gp6HZy1tMXvk8xzxHJyY38outwVfc+r8TMb+mMX+EWGJpffkI9Z63yXc+/gDkfGW1jrHnvEuYsbPpkjGMZeG93vG2o4iI57xr2c1Nf8jfwDGYKuzUpTVIQAAAABJRU5ErkJggg==>

[image44]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACwAAAAWCAYAAAC7ZX7KAAACAElEQVR4Xu2VMUhWURTHj6mlSLgUWDkYmoZggyi4tDsELbYlGBlCoKCLQUObBEmzCjqrc0NDg1BoSRhBQUhQgpKooYiig1j//3fO/boe37Oc+ob3hx9+73fv9zzv3vPdJ5IlS5b/lhbwAuyC92AQlB+ZUWBZAp2gEoyAX+DjkRkFlAqwABrsmiu7J1p0QeaSaHFPI7durmBzB5TY54vgUP694HNenDJlXpw2vaLFbvqBKO3gC1gT7Xnu0ijYAt/AI5s3DhbBT9BtjrkAPoEV0fvwoR+DH6K7O2HuCfgMvoNn/GKccEpsgDY3lpY+0YfjA4QMmPM7xOtp526Yj9ux2dzzyDWZS8yQ6OCUH0jIQ7Ds3APR7686T/fGuUbzdZG7Zu565GrMpWZWdELo67T0gNfO3Zfk4uh43zg8meiLI1drLv7f1eZyuSl/ei6kX3TCsPM+7MtXznVJesFzznFlD5yrkeMFV5nL5atdtOaHtdnp+MY7Kdx+X/A9SS/4rXPcfl/wVTlecDh6c5kHO+BKflhkUnRCfeSSwh6ece6kgt85F3q4KHJJBV82l882+ADG7DOPKxaTlruiN4h5meC4+h0JPvRkzH6C4+rzCAzX+fB1fFv0SLolf38ZnBU98M+Irk6p6Cs+OIaeLswNjnM5h2P8sdHx7/nIMcGF8SxZfH4DLl+J5nskRqQAAAAASUVORK5CYII=>

[image45]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACYAAAAXCAYAAABnGz2mAAACNUlEQVR4Xu2WO2hUQRSGjxgfJCBExAhaGREUQRRMYYyBiBrxUYhIUARtxcIHBCwUWyUQSGXAIKKVCGIp2ARfjVj46gUxAU3whW+N/7/n3t1z/8wuQlyIkA++Yv4zOzt3du7Mms0ww//Ffg3qRSd8Ax/B1VJT+uBZyZbDcfgFPoWNxXKJWfAZ/Gb+XRuL5cmsh9/hBTgBLxXLBRrgCGwN2Rr4Fq6De80n9gQuCn3IINwO2+B5+AseLfQQbplPiF/4Gx4olgvshPdDm6vASVwM2ULz8W6GbJ/5akbY56dkZbrNOzzQQhXew+bQPmX++ZchI8zowaz9Ef6olEs8Nu+T5Jx5sV/yatyQ9gmrTCKSZ/nq84G0z91EZu3mv3E+AGV7W+yUYI+0l5i/MHz6SD7m2qx9Er6qlEuMWWJi8+BKOGpe3JW1Z8dOAutzNKwCx3yooZBa6TIs6NOm4CbXfZSiBb6GO7QgnIG3zRcoCSc2pGGCLvhcQ2EuvGe+0Wux23zbzNdChBM7pmGCK7BXQ+Ga+b7ZoIUAz7pP8LIWItwvnHmTFoRD5stei8M2+cbgW7cltBfAgdAmsV6Gb8wLDRPcsdqHLgfnKmzK7DA/UHmbLM368Mbgw+V9KE+A61m9wBF4VcME7yx995FV5vV47OR+CP14HWm96lvJq2WFhgk2a1AP+CYcN1/az1JLwQueR0XdOQ2/mt/wyWUU/vaqmjLLzP+i8M5bLDVlKxzWcDrAP4M9Gv5r/gBiGIAugjWq0wAAAABJRU5ErkJggg==>

[image46]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAD4AAAAWCAYAAACYPi8fAAADA0lEQVR4Xu2XW4hNYRTHl/v9GnJLisglCUlezgkvSkpu5cWUKZEQEUWdXEp44kGUZh4UQkpIXgwpXii5hNB4UG4pEZLb/7/X951Ze+19ZiQPp+b869ec9d9r7/2tvb9v7W9EaqqpppramXqDBuf1cDE1zxvQGHASfAB3wMr04erSU3AIbAAHwWvwI5Uh8gVcBDtE866A36kMkSngI7gEOoJl4Gsqo8rEAiyfwNJURjaHXE1liNwDb0Av45XAAhNXlbZ5I0ffvJEjPoy9zusHfoK+zq8K/c/C/bU45ekXnZ8n5v6rOnvjb1QKvAD3wVrQwRynWPgs0bX9TrSBjU1laIGbnEfRr/Nm0E7wRPSabJYF0Xt8BjfBTLAQ3AKvwGkwKjlTdQE8B79AF1Af8thcz4BOYAt4AJrBgeSsoPM2gJok27jY7KaZuCia0zXEvCnjdTHBiD4LbE2XRQfMpRH1SPTc7sZjD6E3zngUPTbfqCHBazTexOCVNcAG0G7JFj7dxSyUa3d5iOOUrlT4dm868c0ddt5tyY7jWfCKzqe32MR8WPQKxhsZvIpaI5ow3B9w4tM/ZmKes97EUZV8K866zc7jVPcDfRy8Oc6nZ18O1zy9EcYbGrxEq8CplmOJYuFxDXNDwyJnlzNU9E6YmOfsMTHFbk5/kvO9zkp2tjRJtnCuVXpznU9vco7HYqMGBS8R1wUD++3dFbzYZWeEeH85Q6c61719k8w5bmJqPHgr2WbpdU6yhV+XbOEPg+d3jb5w3s8XPjh4ifaBjS3HEl2T9A37iHba0cYriOYMNN53cNfE1ArR3WBb4hr347gh2cJjw8srfKqJY88ZZrzY8Mp6KbqeGkQ/CxxEf5sAHRXdyvJzwin+XnRLasV1dUT0AZREB0laU6PoYCx1OR53f7HZRfh5bc7J5afQe3Gak7K6gUVgq+h+u5ImgNVgiei6ryTm8Vrzpe2NRU/RZcOpybfEsZDoUfwHiTGXY/T4fea1OY54D3rM4Qzlb+byL3Pi75pqai/6A0pLyJIzewmAAAAAAElFTkSuQmCC>

[image47]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAD4AAAAWCAYAAACYPi8fAAADFklEQVR4Xu2XS6hNYRTHl/fbLXnmkfLKIwkhqXvCRMmEKBMnKRO5IiLUHWCAmYGQugMlIXnLQJe8BiiFKHQn5JUor7z//72+71hn7X3uvUyc2P/6d/f67bX3/tbZ37f2d0Vy5cqV6x9XLdwIv4evwkvhNjYB6uJiarYH0DD4IPwavgkvKT9dXXoDL4MnwC/hH/CxsgyRD/ApeBNcB58TzbMaD7+FT8Nt4YXwx7KMKtIguGjiqaIF+aIisz5fliFyG34OdzOsHp5r4qrRSfgK3NmwbaKFjTXskzmuJF6z1bEa+Bvc0/G/ruOiA55k2MbAxhjW2sLXO8YpT15wPEvM/VO196AlFUTfegfDDokOtpNhLHya6NpmH2ADG27OU7xmtWMUedHDoM3wA9F7slnWij7jHXwZngLPg6/BT0THNiS5UnUCfgR/F62BvYp5bK6H4XbwWvgO3ATvSK7KEE9woI8d/wpPNHFBNK9jiPlQxitighE5C2xOZ0QHzKURdU/0WrsM2UPIRhpGkbH5RvUNrMEwzmCyTH0RHcAIx+1SoFgo1+6iEMcpXanwDR468c3tcuy6pAf6MLCC42TzTcwfi4wzKIqN3N8v0WDRN81vcWvEX3+viXnTlSaOqsSt+Plc4xinuh/o/cBmOk5mXw7XPNlAw/oHVhKTzsI3LIT6hb/dRYucbs5RZAdMzJtuMTHFbk5uvxBZOiLp2dIo6cK5VslmOU42LoOx2KjegZW0T7R52PXFptArHE8WvWD7r9PJVOe6t2+SOftNTI2CX0h6J+h1VNKFX5R04XcD87tGXzif5wvvE1hJT+E58AzRNcGbshNG9RDttEMNYx5vEn8c6jN8y8TUYninY1niGl/l2CVJFx4bXlbh3HlGxZ4zwLDY8BJdCEGWrfbAz0Q/J5zir0S3pFZcMrtFf4B60UHSzalB0s8tZjDu/mKzi+bntSkjl59Cz+I0p39bo+Hl8ALRdV9JzFsnOota2lh0FV02nJp8S9w70JFR/AeJMbfCkXEp8t4cR3wGGXM4Q3nMXP5lTjzOlet/0U8wa8xOHI9VkAAAAABJRU5ErkJggg==>

[image48]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADUAAAAWCAYAAABg3tToAAACpklEQVR4Xu2Wy8tOURTGl/u99CmUcikxMCFfiPJJiDAwohBKJkqfS/gDkNuAgVAkBpR7GcitZMKEJJeUCeWW2wTlEp7H2vvtOeu83ysDdcr71K/33c9ZZ599WXudY9ZUU0019RcaBo6Bd+AeWFS8XNMqcBc8A8fBmOLlauk9uAFGgXbwE2wuRJgdBnfANDAE7AWfNaBKagFfwEDxzoHv0qZegH7B4251Dl4lxNW/ELw55rvVSbyP5jupWghGBq8SegNOB6/NfFI6YLZfgvniXZT//1Jdo/EnvQVngzfdfBIzxWM60iODwB7wWq5HMSYXFe5yX7DNvBA9B9tBF3AAPAEfwIrfd7qYLffN034LGGFezNjXI7AUjDXPsqfgOpjCG6kd4GZuJO0yH/wS8ZiK+5KfOSXXO9IE89j14jFtcx8qtjlw1UbwA7SKt9/KmcSNqfU32LyKcSUpHvzHKWBBDoLOm68oB/ktXSfdJKaeOBjGsSBlzU3eJ/EoepeDt8F8x1V50VVHo/cVnAQDzEs1d4ABEyWG6TE0/edAH5rH8BXQSOOtPIDZyWMaqehdCR53mNVYxdSNfR6p4xW00ooBbLdJO6uPeT43EvM+PmxG8nhmVPUmxUWLhYxnLPZ5SD2mG7dY3zcHrXjTYjBZ2qpb0QgaZ+UBsAB1NKmrwVtr5UlttXKf/DioeVNTgxWP6m/+hXE7B5hXnp3SzuJObYpmUD5TqlnJexB8eteCxwU/EzxW0dhnYVLUK3DCPC95KEfrxSROimWdJZmx/E68VIgoarj5QxQWmknB407PqxO7vI6XU0zh+dot7ZqY96vBOit+RUSxUi4Da8wLQCMxnbmTfBdRfIGywvI3e3wWY1hBe4rHdo8E+6HXHfQWj6LXK1HJz7Wm/iv9Alj5stKJ/KEzAAAAAElFTkSuQmCC>

[image49]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADUAAAAWCAYAAABg3tToAAACX0lEQVR4Xu2WT0hVQRTGj/03W0QE0Sae0SIJxDAkSAWjon+7kDAIdOFeU1q0E1SURHClkCK1qIWWQrWpBJfZKtTQhUiGRYtAoqQiMr+vmZHjuRM+Aukt7gc/3ptvzh3m3Jk5c0VSpUqV6h+1FyyCRuPvAZ3gHVgAd8DhdRE5rH7wGzQb/xV4Ak6CIXExX9ZF5LA42VhSU2CHaj8VF8eVzWl1gFFJJlUKvoJq5e0Ev8AD5eWcisWdpVhSx73HvqA88APcV95maZs1stEWMAFqJJ4UE3gLLiqvSFzcLeVpHQCvxRUWrjILTTuYBO/F7YqtoA/MgSVQ9+dJpwtgGnwAraAQ3BM31gy4DkrAY3GFaxyc4oNBH0HG/48lZXUQfBYXt5HKxMU1Ke+q9+zzbHPiWjfBCjihvF5xsUeU98h7a7qh/meTFKsgY/i2NxInw9h9yrvkvWXlUfSeGY/z4Ipr3ZbkC7mrPR5+boOgbJJif4s1/yIWGTuB897jNtKi99x4XOER4/Fl2jEHg8c3xqX9rmBFY+dPSb610+Cb8a6YthX3vZ3AGe/xzGjFkmoAw8bjGbNjhvtVCsBRw7zv5NfDIf8AdQx8AteUR3WbtlWonFpnvRdL6oXx+GVjk2qT5JgDEW9Ns+I67fZjhekB5aACVIlb6XodFFE4U1rnvPfG+PTGjMd5PDQeq6gdM5pU2BKacd9XGekL7PcxVhlJxrJ08zNLey/B5UhsbcQLW0zD89Wl2psq3n3c3qEI8QLlXcXf4PH+Y8x2sEt5bPOLhXAcevxE2608il6+J3ipUv0vrQJujbNaVtkucgAAAABJRU5ErkJggg==>

[image50]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAD4AAAAWCAYAAACYPi8fAAAC0klEQVR4Xu2WW4hNURjHP7fcqQkReaDIpcmk5MHluLzI5EUkL+bBi5I0mokH0yhKuYUHL9Q8KLml3PKIFClKIYoa4sElJUqUy/9/1vrGt7+19zGUOjX7V7/OXv+z9t7r23vttbdISUlJSR9iqQ8iw+Fe+AK+hMfhlEyPwFR4Cn6A9+CG7N/1xXhYgSfh/uxfPdyFV+F8eBb+hJ8yPUQa4Ud4BfaHa+GXTI86g0XwTr6W4sKfwMGmzeK4X4PJHsA3EmaH0gmbTbsuOSf5hc+Fn+E6k/EifJdw9xVeiD2mTUZL6DfK5XVFUeFNEoq6ZLJ+8Cs8YzL22W7ahFOeecXlebDvvzLQB39DUeEs8hVcabIZEgrqMBnbraatMG/xYWQnfArfweVwMbwmYYbdgvPgKnhbwqN4Gk6u7hm4CJ/DH3AQ3Bj7cXHlbBwA2+BD2A33VfdyFBXumSBhEWNBCk/K9maTKcxZYC24cHLAfDSUxxL2HWIyriHMppmMMLts2uNi1mWymTFL6G3hPAEPYK+eTumiwnf40ME7d9RldyQd6LOYVVzObLVp82Ix4wxSJsUsgYUf8GEO3HmXDyXkW3woxbnlAtzmMk51P1C+XZj57w1mXIQVPvPMJpqMr21/vCos/KAPDTyZfy+vMds86G7TJlzNmc9yuYfn9rPluqQD5bPKbJnLmc3OyVisMiZmCbUK58Dfw/UuP2K2edATpk2mw7cSFshanJe08BuSDvRRzLgQWnzhPJ8vfGzMElj4IR9G+IFzGC6AC+ESCav8JtPnG7xv2oQXqjfrBp/xrS67KelAdcHLK3yOaeuaw4VY0QWvBzbyVBbl/KfaK8rn6piEC9ApYZC0Fl2SHrMlJ2uW34udys/n7py+fBX6TKc5/W/wHd8OV8ifPyyGSXgVcmryLvGLkGpGhsY2P4U14/uZxx4RfzVjn5Fxm335yz66XVLSV/gFwtfAsUjV2rEAAAAASUVORK5CYII=>

[image51]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEIAAAAWCAYAAAB0S0oJAAAC1ElEQVR4Xu2XWahNURjHP0MZylgXT/IgU6YuSqYuEQolGYoHupIxSknygiheJBSFm7HIi/JGHnggeZGSB6EMGQshM/9/39rXt76z1zn7njzuX/3ae33rW+vs/e1z1tpHpKSkpKSkbmb7QKAr3A0fw2fwFBwWZaTpD0/Dt/AB3At7Rxkx0+Ef5+ooI2aJVObnxehv+At+gfdggwTawb5wCmyBx7IOx014BU6AJ0Un/RplpHkF98NGeEt07NMoI4ZFHyKa/0E0/06UEXMdPhHNGyc6tls4joDnQ9+sEBsJZ8Cj8I0EnockXhhNFeIh7GLa50THDTCxPFjos6bNOTgXx7Y38RSH5N/TTHEXXpR0zlbRvtanb8gdc0byCzEKfobLXPwjvOFino2ixR5uYmNEL2CXiaXgT2KVaH5n10c6it5gkUL09B2SGJMqBL9eHHDVxV+Ifi2rsUF07HYTGxRiO00sBQvRXfRBLHV9ZF441lsIrhkVpApB+FQXmHYf0UkOm1gezLsPB5vYQtEL47EW2SLJxfma7QhcCsd6C5E7plohLL3gS0lMUgMutizgT9+RICsE1xp+3h7TtwXuC+dtLUQP2Ay/mVgrRQvBxY8TF8n1cPvk9rXcxVOsMef8TP4cO4Q25xoazosUgrsXHyCPvAaucdxBKmAhjvtgDpz0gOhTagvcJb6L7vFFWWvOefH87Lmi2z239IwihRgP+4n+XLnuJK+fhTjhg4aJoi8ilhWunWKz6DuBZZpr57HenC8WvaEfovs/byajSCEG+o4U1QrBxe41XOniF1w7Dy6KfKsc6+L2aafgrpPRCb4TvSkunpb/XogWHww8gkfgpGATnAl3mJz5oi9ll02MfILrRMdNhlPhnHCsxSbXPih6U00uXqQQdueqIHvlzTODK73vyxxt8hbB9xJvc9ukcoyf35P3X8Pm3zbnqVyuQz7m5ykpKSmpyV9Dqd50/79S6gAAAABJRU5ErkJggg==>

[image52]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACsAAAAWCAYAAABZuWWzAAACEUlEQVR4Xu2Wz0tVQRTHT5IKEWFIkNBCMi2jNkH4a6OE4CqEWvQPiKsCCVy6CSKIaJPoQpRCl5HiRjdBoAt10UZoEWVQpCsrLAjU6vvtnHlvZrz3vSuKq/uBD8w9c2bmvHkz9z2RnJycI+E8fA7X4Vt4F1YHGSGP4F/PXdE50nglYf5vi/sx5x+4LVrLS8sL+AqHYAPshh/hfJARcgY2wy74Q3SRB0FGyAcpFnMFNlmcc/RYnIVdMltgP/wMn8EKy//PoP8gWrT79OUYEV2ME6fBjXDFJsH4kzgIzon2PXSBVjhR6C6yHAdSuACnJb2QTnhcyhfLo5VEMK7OHibhaYtdFT2HWWCxN0Xn4PGIeSGHWKwf4KHmmVmDw35CCVgsi9mA96O+U/CLHLxYXroCXHDTOug3eMtPKAHHksuiY9u8viV4XfZfLC/UNfgGvoYnvD75Dh/DdilOup9j4OC4MWvz1q9aO0uxP0W/Hco2d3NFojfBRfjUe+bN2xGd4KQXT6PRa3PMlug4zumORZZip+BZsxZWBRkGz1QSA6I/DuVw70zCBbnwIpzx4lmKdd9ISd7HAaMD3o6DCfjF3pBiUb1e/NCKHRfd+hjubE0cTIBvD8cx+El08UovnqXYiTiYxjvRQz0LF0QvXF+QERL/N6Bz1lcPf1mbjMre3FL/DdI+UAHeuE54D96RbDuak3PU/AM44KIBqFzkUQAAAABJRU5ErkJggg==>

[image53]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAF8AAAAWCAYAAACmG0BRAAAC1UlEQVR4Xu2YWaiNURiGX/OUIXNJ7RtFScIFyZBEQglx4UKuDYeUXCuJKxdk7ihlyJAhmYe4IERxQ8g2Ry4kswzv61u//f1rc7Z9LuQ/+3/q6ezvW2vvc/a31r+GA+Tk5OTk5OT8U0bQ4/QdvUwX01apHkAHuoo+pI9pPe2X6lGiPb1J39J7tFm6uYyFcaKWUIFmwIq2i36nF1I9gCuwAdJA7Yb10WDF9KG36Djaho6k81M90hRgg1STdKTXYEUQvWGFlZ7btK2LD8H69HS5zvQBve9yR+lZF8ecQPnvqhn6wr788hC3pN9CLmEobJbPcbkW9DM94nJf6RfayeV60K4u9jyHPXE1W3yhAjQPrweifOYPDvExlxNv6GEXq88dF1diBe2Pvy++9oYtKP2tMZoQ2+JkllgJK4Y2Vk+RTnVxAdZPm3CC4jN0CH1Kn9H1rt0zGbYnVFN8LXsn6Q5YoT2Kd9KDUT4TnKPvYUUfELXFdKevUF605IkZ73J1dJOLxVq6ObyupvgJ7egp2BIp9PMAyk9omWMjbO3+04wVe2EFi/sop0HxjIbtA71CPIw+oV1C3JjiCz0F+2EntH1oAoUXenzvouGCqG1NnITlL0a5ZL+YHeIbdGapudHFFzr6voCdvDLJWNilyrMaVpAFUX4M/RDlZrnXeo/WZM+gkJ8bYp2QPjo/hfYknhT6VcLP/MwuOUXYl/fr/IaQS2arULuWlHkuJ5K1W+g9ujN4hoe8TlFCM92rC5jak1g36Upozdcg+zVfs7/1rx4Z4Tp9Tbu53HlYQZJ1WRTpOlgxdcsdRSfQJa7PS9h9QLMxQXeDSy6OmYbqlh0V/jTdE+W1D+nYm7kB0PX+KuxUohPPI6SXE22aKtDvLJS6/WQZbCmphw1YfGT1xJ8lp6R6pFlEt6Lhc/72OPm/o0d9Ol1KJ6L8DF0t+v+Obsya1Zlci3NycnKaGD8AGXOo8LGrXi8AAAAASUVORK5CYII=>

[image54]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADQAAAAWCAYAAACPHL/WAAACNElEQVR4Xu2VO2hVQRCG/2gKRYtEBAsRH5EQiU8EMSDGQtHS1lgEezuxs1hQEAU7H4Wg4CMEIlYGBBGsBQsFwfKqGAiGiIWvwug/zC53du6uuUi0Oh983LMzc+acuew5B2hoaGjogiM+EFlFL9K39D29TQezipxe+st5N6vI2U5/Iq8Pbm1doD/oK9oPxzo6Su/Qqy6XeE4f0xE6AW36NavoZIgO08/Q+m95OkOu+w5ad4Buo2uhPXbQBzF3OMZ2xuObdIbuh0EKW9B/vjbQG7rCrB9Cz5M/YzGm6EdofQ259hXUa85Bc30+AY1/8kFhEuWB9tIv9ISJLaPf6SMTq3GP7oJeeI/LJWSHBCw+0GqfQHsbdlAbaDf0BNlylnk67WIlZCDhBcr9N9Ie/MeBhA/0uFlvgDa5ZGI10kCnoVvDbl0hmN/ijeEfDGSRh3UOlSYF0kCCnPPUrOWt+iQeB9R7+oGWQ184F6A75WiMZ3Q7UHrj3PCJCn4geeVujmu55lg8DjFfIg2UlB7yDLfo+nZZjjS/5oMFpOFl6L7vhvvmOL2az9M1dJaujLkQcyXSQJtc/I/IQNd90HAQnd+Sk25dQr5biQHovys395LuM7kQ4yWWfCD50Mm35JSL33LrEnYg4Rn05l67eIjxEn89UO25aEG3o3zFxUP0GD3bLqkifS3j0Js74+Ihxkukgbb4RIn0oHkTstV8LrnV1Fl60Vlre9qdIG9NXyeGQsz3aWhoWCJ+A6ojtwQfjFQEAAAAAElFTkSuQmCC>

[image55]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEYAAAAZCAYAAACM9limAAADMUlEQVR4Xu2XWaiNURTHl3nKTCTCg0hIhmS8phIPHgxJeZESRXhThjwYU4YiRUiUknkqeeFBlAeKQuHGAyLKkJBp/dp7n7POOt+5Xfcqbn2/+nfO+p+1v+/stb+9zj4iOTk5OTn/lDeqLaphqjuqX6pHJRkii1Q/VRtULVXbVN9tgtJedU/1MMbDVdWq1oWMBkQj1X4Tt1O9lFAcyxfVeeddU3Uz8V4J4yhwYqJqu4kbDFWq3s5bLWGCQ4xHvNDEsEq1zsQU75mJEx9Vrbz5v8PkmPRK442N3uIYt43xyEJGYLLqq6ppjMm5VPy4AL4tYCXSdeoCT35jb9aH7hL6Sh/jLZUwmTExHhxj+wTBuOj3ijHvTxc/LoB/0JuR6ar7Egq8UdVXQo/6pHoQc4aqLqjeSti+LFyCgtMj6XdTVVdUTySMTws5S/VC9Up1PHp14oaU9phUgEHGAwqHzxcH3p8sflwA/6w3I/1UyyTkMHkWCXpI6HXLVbclLAq5H1TvYw5MkLBVGX9Mios0RUIh1krxO82LeXXiueqbaqbx2DJZhRkd/bQyNRUma4tZyLnrPJr2VecdkfLJXYzeLufjrXEePTDthFrTTPVZNcP5oyTcxG+l1IsGxpj3lbbSCW86yDnjvK2qfc47LOWF4UnDW+F8PJ4SS7WUbsVawU3ZNp6eEm4ywvmTos/5BXjP6nnwd3rTQY5/2jar9jjvkJQX5lz02JIWvDnOeyp/UJgFEvYjTdZitxM3Ic+yREqbGTmPTZzA7+9NR1ZhNkl5YWji9SkMjTlr8TOhg/PTzACaGY1rtoRml+AmO0wMB1TTTMyp94eqo/FoojdNXAmuf8p5PDEcGi1ZhUk9hkZtwZvrPAoz3nmZDJBwgSw1MXnXVe+k+LPOE8CvgYWCMs5uG4rnzz8Wzi6dJIy7JeH4QK+juEdVl1VdVc1VnWNMbpeY10LCrxbebgnX4y8L18Fbr+og4YBJS3gt4Uln+//Vc0+VhMMg/4MqwZfm9DxfwuGwJpgYAg5pFICJ4fHFER4T4zVNhs/J438Y4yDltpFQtOQxFo+ikcuCM84ufE5OTk5OTk7D4Tdtar1iYEc+qwAAAABJRU5ErkJggg==>

[image56]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAIAAAAAaCAYAAAB/w1TuAAADh0lEQVR4Xu2ZWahNYRTHF1GmlJQXwzVThgyhlFKG4skLmW9kKjx4MjxdMsYLXkRJhrzIi0QhtwwhIZF5ypRSxjyY19/6vnP2/dvnXPfuc/c+R9+v/rVb67v7v7/vrr32t/cRCQQCgUAgEAgEHN1V11S/VMNVPVXdogNKTGcxT/g9EPNsSr9yoa1qrti8oX5i69A+MiYTmqneiV1UWsATfhs48Z+zQmzeXzmRJQMlX5Vp4T3Hc+I/54jYvM9zIksOi13UOU40IfBM069c8DfaOE5kyUuxi1rPiSYEnmn6lQu+/bfhRJb4qkyrHfeRdP3KibJr/wAXdZGDMTRXDVNN40QDOST/vt+4rHqjqqV4JeILfyInYhiguiM2/oXqhGqd6omL3VdNz41OCE64mYOO3WKvhZNV91QnJbnxcyleAPADi8TeFtAusQCDciMqkwWqb6p2nFBGqjZyUHkltgae0VJ87RpMb7ETTuKEWMXin4U739NfkhWA9ys0CXh6v6uqVu4Yd8Red1ypHBTraHEgh4KP0lp1gGKrpPDaNYqFqh8S/zFip2orxZIWAPwwAXjGAU8PnpX+bkFR4GNVJYNWzuvp+ajqQLGxqnkUO6X6QrFEvFbt4KBYG77NQSleAHhW75e6LYuBHwqAPeGHZ16cJ8AHFH51qhbzLOSHbw13VVc4EaGX6obY18k4uqiuq3pwwjFE9Vh1iRPEErF5d+SE2F09lYPKadXTiPzarc2NSABa8RyxEy4Tm2hX1RjVFrGKXJMbnadYAfjWjnMwqO5o+4cn/BDDePghHufZSfWWg2KLXsgPYF9T7HEDfEtdygkHrhP5lZxw1OfRQqwQ0c0wBusMValmqS64uH/UefB3nym2Wmws3wiN4rvqp+QvPk64OxgUwAwOOj6IfVJezAnloZgne0SF62HPlqqzqk0UB/PFPOP8wFCxPcwtTkTAfLCjruKEA3c+8n054cDvGPCIK1BQLfa447mymFHyd/y42CYSvylkBhZsJgcj1Iq1xVJREzk+GjmOUkq/xlLDgYQcU32iGApiG8VSBwUwm4OOwaqbHEwA3pf3OWE3vD2adMAza7Bbf8TBBKDrvVedoTgKYArFUmOE2CsMdrK4OGysuBNgs4TvBaUCm6tom1xeN/2nFcIza/aI7ZtKBTa2mC86AB5BE8S+wSD2TLUrPzQQCAQCgUAgEKiH3ylb28lDk7K/AAAAAElFTkSuQmCC>

[image57]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAaCAYAAAC+aNwHAAAA70lEQVR4Xu2SPQ8BQRCGx0cjiBaJaCSiUui0FAoRBQW1n6DXKRSiItH7BRr/RCJ6lAohkeAdu5tbc3eiUN6TPLm7d2Z2s3dHFPB3IrAIr/AJF7AEy7AOb/ACG2bADx5mKyIf6/wkchfcdIAhkY90jf0KN3RkSM7wShZssvAOU/o5DqtwRmp4ozNf+vBB6oWxZld2AMNOqzc72BZZl344N5Mh1chXm5rOEyJ30SPvnYak8rQsSJbkvcCaVB6VBZsc+X/jI33mLev+TR5OyVmgAGNWfa7zpK7trdr7XPzZzLCR/30DLzaBZ7iFTasWEEAv2tw53rzh/OsAAAAASUVORK5CYII=>

[image58]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEcAAAAaCAYAAADloEE2AAADSUlEQVR4Xu2XW6hNURSGh2tIQkchcSQhcikpD9hJiTwg5QF1ELkcPJHkRR6QS0lyfaDIvTxIFIryIuRF5JYiyS13uRt/c25rrn/PteZau8Om1ld/Z59/rOtYY445p0hBQcF/zBQ2asB8Nv4mLdmwDFUNZrMGTFN1ZzNEc9Vs1U+r3qq2NtZF1WD95aoeqlY21kI1RPVRtUzVx/ou51Sn2fQwSvVNtUvMvdbHw0Hw4jjvvSR/JHBXtZvNEIMkSg4zQIw/iQOWWWxYJos5r0S+jwsSvdxX1YR4OBM4/yybxCLVD9VwDqTRTZKTg6TA9yVhPBsO11TX2fRQp/queiXmOXKXvgXPuIpNop3qheo4B0Lgq3FyGlXzVG9UayiGobSDPBdcC8MlxCYxx/L181CveifpQ6oMGjO/Z5BHUnkSegZ60kPVNsfH135g/ybxWdWGTYeSRNVaFipohHNMVuZIvLftVT0Vf+UOlMr3DHJDKk8q2b+IHXR8NE5UVRq32CCQuP6q12LuO1bVV9XMPSgjB1Qr7G/0SPQ7DLG3v4+IwMfGR8jFCYkn55DzG7Erzv94kTS6qk6x6WGimHte4kAO+kmU3JOqDlb4mOuc41xQ9bnYI1FyRqs2OjGU6X37e6bjJ4EHdistCXxd3HMrB3KwUMw10GiR7NbxsBdMFrkqdIOYm+CkM6qOTgyJQvm3V91z/CQwPLLMCEfE3LOB/DwcE3ON/aovYvpjiJtshMCYLT/o4nhIVopZH2yRbLMKpuPzbHq4LeaeWExWAz7kM4kqHusj7ps+nrARAvsfXBilyUwVE5vOgRQwW4TANa+ySWC5sIRNywIx10BDBr3s/wB9DzMwgxGRJYExxkjySehBF9kMgGvVs0ngmJ1sOmBGwzFYg5W3NC5ICuJz7f/Y2rwU03f2qZZa3yVrdcXAFOib+gB6SN7NIx5gBpsEjgk1eEwUSA6aPHNYzDKjk+ONE7Pa3ixm2mbWShXJaWoww31QdSYfPQtrJFTFZYol8Vj8L5qXYRKvtJrRU0xyeL+Dh8N2BFuLUGWV2c5GlWAY3pFs24w/DirkOXlIDmY/rIOyVAOGOzakTcEn1Ug2awkSsJrNGnCUjYKCgoJ/hV9BlLI0/lK7AgAAAABJRU5ErkJggg==>

[image59]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAsAAAAcCAYAAAC3f0UFAAAAz0lEQVR4XmNgGEFgGxBfBOKnQPwRTQ4DRADxHCD+D8TH0OSwgl0MEMVe6BLogBWIvwLxHyDmR5PDADYMEFPPoEtgAzUMEMV9UL4hEO8G4rdwFUgAJAFSHADlg9xvD8RLgJgHpggGQAqvAnEUEM+EihkB8Xq4CiQAUvwNiG8BsTmaHAYAKZ4AxBuhbElUaQRgYYAEGR+UXwHE8xDSqKAIiLuR+P5APB3KjkcSB4O1QOyNxFcD4gVALMQASS8oAOROTjQxUIJ6CMTBaOKjYDABANGcJ5sC3aSPAAAAAElFTkSuQmCC>

[image60]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAmwAAABDCAYAAAAh8FnvAAAHLUlEQVR4Xu3deaxt1xgA8GWIqeYpKkRpxRRaNSSk9CkiEVpjSA2tmFMqbcQc9Y8hUf+gJTG9CGqsGqKRhkhMEURqbgVPioiEIEgEZX3Ze7nrfu/sc8+55w7nPb9f8uXs9e199rnv3Jvs9b619tqlAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAwEx/qPGfGj+rcaCL02o8usZjazyjxoU1rhmPjbikAACwZ1onbFFPK8sdv1dOzAlmuk6Nd+ckABytTs2JFd09J/bIfcrQAftg3jHHbXJin30zJ3ZAVBa3ElXI3fKynOjcYIztisppVFEB4IjQqkutYpTb53bt+4+58Lduu3dyjd/WOCXvSH5SZncy4vP2w6Vl+DeekHccAW5W4/KcXFF0lo7NydGVNb7ctf/ebW9XrnLG7+N6XXuWr+XEhBfU+FM5vEO+jlVSAJjpYI1fply+kP08td9Q484p18R7v1fjVXlHEp21J+VkdXVO7KHcaThS/LTGjXJyRT/OidEvahxf4x9d7rhue7tuW+Nf4/Yty+JDlrfLieSMGq8et29a47rdvrfUeHzXBoC19Zoa13btB5TNnZY71bh11w5TnZqHlOGCvoipc9yqxkdyco98tQw/1+/yjjU39V1uV1Sibp6To6nPiirWKi4qQwcqHOryW/lNTiTxt33jrv3ObvuYGr/v2gCwth5RNi7CUaWJaO0YkopOWO+uNT6acuFuNa6qcWZZbFjxn+PrJ8e4RbdvqlOwF6KyE5/fV5BWFZWdz9f4Rhm+08tqvLUMc8Ti+37OeFwMbbZ/+8HxNdxjzMf3et8a55SNTkicbzvf13k1rihDtTQm4ffnmDpfVNbi9zbr9zv1nnmimhpD6C8s8z8//q4i964a7y/DfyqafGyW97cqXpP3A8BaiqHNdtH63PjaLmq/Gl97T6jxxpwcLXPxe1sZOh4hOjC9Zc6zG2JOVvwM78s7VnBSjTuM26eWjQ5r+H63HRXNph+uu2cZ5g3G/MBedJ7+mnJbOXt8/UyXm9dh6uV5YM3Uez6UE6NYFuXirj3v8/u/0f5nDvnYLO/fqg0AaysuWlHpaGJNsqhiXL/LNc+q8bqcHC168Ytq3CvKcPxN0r6w6Hl2U/wMX8rJFURlrHlojV937R9029FZPrsMc62e3OVDzPt7U8rdq8afUy4qelPRxO+2dSCjkxiT8pt53/+BnBhNvWeqUhnHt/lkUZX9Yrev78w2/VBmrx/OnyX/XPG33cv7AWBtxUUrOlDNF2p8rGv3HlzjAzlZDh9Wm+fD4+v5Zahi5YnjU+eJC3l0aGbFrIv8dt2wHF7JWlXfYYth5r7D9sPx9Vs1Xt/ln1I25nXFfKtnlsO/m8jn3CJe223H5z+sDMO0Yep8D8yJztR7pvTHH6rxoLJxo0M+VyzfMbWMSj42+2MZhvGbl3fbYav3A8DayBetGK6cp6/GNLGYbMzTyuLcT5yRC08tQwcl7nLs/Tu199pOdv5CdGafXoZqWFSVzirDdxjVxZjcH53DmJMWlaY2DP3ZGm8vwzInB8rGdxbVufjO4k7KJv/+FtEvyxLfd1TfLhjbU+eLOWRTorO5jLixI+bsvbIMnaroJLcbF/Lnx40xU/pjv5LaIf4z8J1xe9Zdyfl4ADhqfLdsXh4hOhCzOnHNI3NijoNluJDvh1hnbmrO1Tpbdg7bVm5fhsn9TQyZnl6mOzdbrZe2rJi79+ycnJBvislz3OZ5cRmqvABw1OrX6YoLeT8Pqxd3Ri5j0cVQd8OPcmILUTlbB9HRbMOZOyXW0muiQhXDs+/pcr1YBHmn5Xl5szwvtaNKF5XeRe10JRUA1k4M5y3y6KJl3Dsn9tCya7+9Iyf22dSTJ1bR37065bll5xftbb6dE53onD0mJ5cQQ6VvzkkAYH29qCy+8OtxZaj+TA0P7qdVnq35/+ZQTgAA6+t+Zeh8LRufjjcDALD7TinD0x5Oq/GoiYibJmJ/RBwbMWuNOgAAAAAAAICjxEtyYnRpTgAAsHPieZZxQ0GsK3ZNjeM37/6fq1M7FhG+ogxPKwAAYAfFCv15DbF4TFIztXRHrq7FwrL9Q+zP6rYBAFjARWV4ZuXlNe5YhoeBP3zTEYMTajx/3L6wxnndvuaksnm9s1jcNTp2/VMSln1iAgAAZfODy79e47Iu2hId7cHroa+u3aXbnvV0h0+k9rWpDQDAFh5Xhspa86luu9d30qaGQ08umytsx9Y4o2uHqeeqAgAw4WBqx00C761xTJe7oAyVsfZA8Xi4/cfH7RPL0OlrXtptn99tN7OqcAAA7JJzavylxpld7qrx9eIaV3Z5AADWyLlluDs0HlPVsw4bAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAr+y8PTkg0uxGNqQAAAABJRU5ErkJggg==>

[image61]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACkAAAAaCAYAAAAqjnX1AAACJ0lEQVR4Xu2WTUgVURiGPzTTQgNbhLiQwJ/ARSgh1EII3LQIsXW4cqdSEAQZESLRxlwIuRM1IiFwERQKUqEEoovyhyAh0J1FYoRgqEX5vpy5cXw9kxOO0OI+8HDvvN+ZOWfmzJkZsyxZ/pkrGiTkEqzT8DCogWc1TEg5XNEwbV7CUQ0DnISfYAvcgtO7y/Ye5kmWCk3wN7woeYi75tqORb/3dpftF7whWSq8he80jGHB3OCKYKXUCGeD035UCweFndZrGOCyubaTWvCoMtdmQAvKIlyHD2EZHITL5g5+zmuXgfdWgYYex+CGuc4zclpv+o08vpgbQyw8IFdpr7mDzcJGmGtu4J/hkT+tHR9kO0QFHDd3zFvwjLm+QkyYO4lYHkW/vGo8oM9alJ3yshL4wtv+G+z4B8zXgsCp1r73wDPchNuSc8ePkvGKPJEsDu4/r2GAHkswyAZzjaYkZ/ZAMq7QEcni4P5DGgboswSD5LOLje5LzkwXTil8JVkc3P+6hgGGLcEgOc1csce9rAt2Rv+1Iy6m/eDC4z15QgsB5izBK5Jn8VqyDtgML8AlqbH9acmUatvnsRJRCH/CZ1pQvtrerxlegW9wBtZKjYO8KpnCer+GATLr4ZoWDgo758OaHw9Kt7kH/RtLNtW8dR5rmAZ8K3GQtyXnq5JX5Tz8LrU4uBb44D8U2uGqZPw6eg5bA7UQxRb/qkyNHHhHw4S0wacaZsnyv7MDw/h0Z274ExQAAAAASUVORK5CYII=>

[image62]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACUAAAAZCAYAAAC2JufVAAAB/klEQVR4Xu2VzUsVYRTGj2kkgm0MF4Y7d4oYSF+QQppoGzeC4cKdtYigRQQuamHW0g9sEYqmGCH4P7RQoVUIFYKilosUXBQUEVKUz8M5o2/njt6Zbq68P/hxZ5535p0z9/0YkTzHmFZ4zoeHcBOW+zANxfA7/GP6zr7BWpclYRiW+DANNaIFrbn8DLzvsqSchKM+TAuLGnfZEDztsjT8hvU+TArfikVVBtkdy3JhEv6CZS5PxCW46rJX8IfL0sIJzxfr9g1xVMHn8AucgA/hWNB+An6Fc0EWcREuw6ewSHTOsZ9pWBhcR6pFi3rm8gx+wteiHZI60Rsr9q7QLYDZ4yAjnXDGjtm+CE/ZMb1qbSEs+JMPQ7hEefO1ILtgWcgNy+65/IVoYYTt7XY8C/thgZ2HrEuWaXAbbosOT0SvZBZ1y7Iel0fw5XbsNxtvJLP/v+DfyAdGcNVx4+TSDekS7eiByyOewD4fHsAm3PJhyAfR4Yq4Ivrwd7AFvrS80fIBO/dwTsbNnzg4dO99GNIAR+z4LFwQfThX0kdYam2Eb8jM0yRZhiOgTfTau77Bw6o/wyXRiTkoukKaw4vAlMQ/nCuT9yfhkWgf//LtjOW6xBeVBo7EWx/mSge87MMUrMj+fvhfmZfMnToJ50U/X0cCd22/s2eDH+ANH+bJc9TsAlrBZsrY/fpFAAAAAElFTkSuQmCC>

[image63]: <data:image/png;base64,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>

[image64]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABYAAAAaCAYAAACzdqxAAAAA2ElEQVR4Xu2SsQpBURzG/5PCaDFQFB7CK5g9gqwewqJktNkMJmXzAJRSRoOJLFJGC8J3OqfwdRxyGK7ur351fd+93/CPSMhfkYBteIEnmIMZGLl752MGoofHXPiyFT1c58IXNXqAUS58UcMjDr/BT85QgUcY58JCGrY4fEYXTjg0VGHZPC/gEO5vtZs1bHBoWMECZRv6bSUv+r4lLgxTDuTN4Z7oYUbduw+TXMiL4Rgswp3o4ZQxC2twaXIbzuEOPIv+2KUN57APwRlW//W56BPNYPOxDgksV9bwM703Nke1AAAAAElFTkSuQmCC>

[image65]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABwAAAAaCAYAAACkVDyJAAABN0lEQVR4Xu2UOy9EURSFV0ShImqPwqPVKNFp0OmV4heQSKYzMxnxAyR6tVKikhClKIgEEaEQlQRBJB5rZx+5x3InU7hHdb/kK87aO3efe+aeAUpKCqCHHtJPek4HaP+PjgTcwwfWtJAKG2ZOaiEVNmxPw5TYwKqGqRjGPx/nJj3QsAnr9Jo+0zM6Q4/pI3zT+1lrc25oQ8PABvyaxEzTBcl26JNkuQzBdzalhYBtpk2yFToYrdvhb2hDWzIPH9iphcCaBmRX1mPwZ1Qkz+UW3qzYMZ5qSMbh/VeRL/SVdnw35dFN55Bd+F7aBz/iVfoQcmUZv3P77Vre4Qv6gWxgnlZXtumdZNZbl6wQRuEPX5L8nXZJVgiL8IETUWZf8FG0LoxZ+gYfeBmyLfhHZ38CJ3Qk5CUlf+ML/ytMmHI4dLEAAAAASUVORK5CYII=>

[image66]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAsAAAAaCAYAAABhJqYYAAAAwUlEQVR4Xu3QPwtBURjH8aekpAzEbFRGZSIrSiaLN2RXVskrULIZ7WL0ApSBpBQGf773nnNzPF1GC7/61On3PJ3uPSI/nAwKWKOqZqGJ4YyEHoSlgrsu32UqH5ZbmGGHGo64vmzYDHFCGxF79m6du0teSmL+Oup0YzHLTafzM0FPdXvckHTLOC6ou6WYWxeqk7wdpFTvdV3V+d95UF1RzHIaOTWTDsr23MBKnsv9YCmI91QbMe87QhZLbDFw9v75Qh4aniW7xEsdJAAAAABJRU5ErkJggg==>

[image67]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGsAAAAZCAYAAAA2VdDGAAADN0lEQVR4Xu2YWchNURTHlzlTJHN4IZKS4YEMyYMHPCkyFN1I8uAJkTElSYYMJaJknhJlLIkohQdDxtBHJPEiUV7w/39r386+y/Xdc+6553Ye9q/+fWetdb9z9l177b3XPSKBQCBf9IP+QDNtIGfMg3pYZ854C+21zloyV3SyetlAzjhoHTmjr2geZ9lALTkEvbTOHNJgHTmjIFUU/T3oIjQaOiN6g+8lnxD5AQ1114zP9mL1gM9bAA2DFomO4RzU0vvMRui1u74u+pl6EiePH6HF7prxfV4sFk+g1p59SfRGnZ3dEdoZhZNXQ0r6QD+Nj2OgVjubCfoNTXP2Aan/6q+UR/IQauauExd9W9GD2IdfnDda4mxWwqgoXPckrIfeGN9V0TF+cfYp6BvUytmvpIqqTUGcPA6GVkTh5EU/XPSfzns+zvwv6LizD3uxbtAcaAY0wfOXYyR0xzo9lkK7rLMMF0THyC2wCFdUcXWR99A2dz3d+XtD7ZyvKfZIVO0WrpTT1lmGOHmcL7pLFdkv2mT4E9gkvGEDNMXzsQL44FXOXuj+cuBnXfyEaDVVYjPUxTod3Da6WmcZWBRscf3ziSuJY+RZSo6Jjom8gD5LvPGRG6LbZnPjbyN6BvHelYiTx4HQIHe9THTHWg6Ndb6q2CT6kJ7OZpIui1b4OOiWRBMYh0fy76Ssg7obXxJ4cHOMO5zNe/GMYNMxAnoAXXOxSrQX/U5HjP+KaAG0MP642DwSFgbzyGbpPrTbiyWGlcQHcEXUkq3QY9Hz55mk+7E6BvoADbCBlHDSjopunTwTq50kklUeS+ADNlhnjeCEPZfSSksK9/hPUH8bqBFcYdxC2XqnIcs8NlKQqHPJAk5WmlXFw5mrk8qK4mTFaSr+R0EyzOMQ6Ktol+ez3djVwnOFCWYnSdZCT6NwbO5CnTybZ6n9/VUtHaDbEm19bC5OenYcss5jI+9Ef/SyeRgPTYSmSrImoinKNRhrJFmDwY5qsugYqUnQStE3AmkpTpRtMNiwJGkwss5j42Fa/L1ixYemZYukb935opNvJ+z4KL5WSstN0Ze+aVr3rPMYCAQCgUAgEAgEAoEa8hevxcEGBtE2XAAAAABJRU5ErkJggg==>

[image68]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADAAAAAaCAYAAADxNd/XAAAB+ElEQVR4Xu2WO0gcURSGDxpFI0YSEdQobJEqGizUwlcrKdOYFGIjCumCRAQFrTSQUrDyhYgoKAmIEIgKYrqkUEELNSRZfFSKqJ2o6H84d3fu3J1Z5q4hSJgPvmL+c2Z37s7cM0sUEhLyXxOBN8pSd8maOrgA+8yCD99hA8yF4/AUVro6AsIX/8sMLXkJd2EbzDBqXryCD43sK8mirOEFjJlhQJrgGlyHaUYtGbNmANpJrsWKByQnlZiFJLyDe/CLWbBghOQzGtUxL55//fl4hw95sJ/keVuFr+FPV4c/j2Evya9XYdRsqSZn7/Hdn4C/4VOtJ4EyGIUbJCv+AK/gsNbjx0d4TLLZ/haX5CxiC+a7y24+kTQOaBk/PuewSMv8yIEd8ADWG7VUyILbsAoOkbOQz3qTTqzhhZbVqMyGTJJH7hvJ5EmVSVisHUfJuUZPuPDHyHpUbks6fEMyeXgK2Uwf5jklfu8juOiRx+HCjJEtqfwu8CDYga1mIQlvyft7C0j2hSd8Qpd23K0y3jzNcFqrpcoU3Ce5K8l4Bq/NEBTCCzOMcQR/wGySNyDPXG7eVHmt03onIhRsxA7CFu34CVxResLP3TI8gYckr3v+AJ4qnVrfv4InIN8F3kej8AzOkeyFEC/45RfU9+qce0W5hfyXIyQkJES4BX2vcYQPm+i0AAAAAElFTkSuQmCC>

[image69]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACcAAAAZCAYAAACy0zfoAAACNklEQVR4Xu2VT0hVQRTGT0mYFQVCKBXlpmxRLVqFhkJBQYs2ucnKwKQ/O2uVi9pFkMtKqEUSQosgF64LIsiIgnIjFK2kUkqzf4ZFUd/HmfF9d3xpTygJ7gc/mPnOue/NnTlzrlmu/0uPQFsYvwN3C6H510/wLIwfh/mSQnh+dQDsCuMR8FxiRfUWnAdbwRPLvl3UG/AAnAPHwHXwNZPhKgc3wSGwDKwB3ZkMsx3gDjiS+NO0AFyV+XIwbL5A1afgKS8yGa4+yy76DPggc9VrcDk1VY1gXeKdNv/zLeK9B6/AF/AQnAKLJU7tN3/uinhnzRdRTJfM83engaiT5gnt4tUH76h4o2CbzIsp7ujKNCBi/EIYd4V5cyGcVbV5ndWId8L8oTrxuLgmcM18F++Z146Kz/BIq8BL81bRm8kwGwebwpgn8dS8Tv9Y9216zfHSTIDjYCnoAT8yGf4Ma5PPU2vNX3zDVIbfVL4YS4M7VymxWTUEvoG9ic8jXZh4/eCizOOxbhSPPYxebB9z1iLzgt+TBn6jW2BQ5lwEd5MdQEW/M/FKVjfYnpoz6IZ5XUVxER9lHkWfvz0nHTTv1psTX4+Wf8Dvooq1xYYb9d08r0I8nga9w+KVpM/mbYO71gB2gn1gveTw+LQf8VLwgjSKxwbMheju14Ix869FyWLxxkJOKZO8AbA6jFlTbLTMUbFFTILbYc4LxFudXq6/IjZXfjNbwaokpuInsAO0gBVJLFeuXLn+lX4BGLCCFJf7Gn8AAAAASUVORK5CYII=>

[image70]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGwAAAAZCAYAAADUicu/AAADWUlEQVR4Xu2YWahNURjH/2YylyEyvCAZ8oAMeSKkiKSQ8UEpQ8qspCQeKF5JeVDygHg0RQiReDAkQ3gxT2Weff++czrf/u5e5+xz73WOWL/6d+/+r7XXXmt9azxAJBKJRCL/Lr+MqsV0bxgmiM6KXoqOiAYlk6tCS28YFotuir6IDoqGJJPrzjhUJ2DtRYNFO0RHXVqehaKfojXQTtol+pzIEWa2N+qBvqIVoofOt9wQjRUNh9b9m2heIkcdGQEN1n2f8IfhN1+J7iAcMI7SA+a5oei6qIXxQoTKrC3LoYPlGsKDe4aoh3neCs3LdtQbx6CFzvEJFWI9wp3Leo10HmfdIed5OHtDZdaVUQgH7KNoi/M4IEP5a8V7aIHdfEKFCAWsHbReA5w/U/TIeZb+ogtIL7M+KBYw9uVT511FOH8m2kKj/lZ0BlrY3USOyhIKGA8XrFsf508V/RA1dj6ZgsJ+bMXg52kAXU3OiZ6JTokmmfRSFAvYKtFq89wMhQlRNl1ET6CBytMEWhhHbTE+QdfvrGqqr2UiFDBu3KxbL+dPzPndnW/hgSOtTMJ3GVjLRtES54UoFjAPT4vMu9MnZIHrPl/ebDyOUnoMZrUIBWw00gPG2VCqzqGA9RZ9QM3ZSf+NqLnz0ygnYMx3GDW/l4n88jDQeDwh3jLP1YAB48HHMwxaX78kTs75bZxvCQVsmeiBN1HYL8f4hBSyBmyaaB90FasV/Mh+552AFlxNGLDj3oQe4VlnDirLAtEV53lmiU6a57m5v+ug24KnM/Rb431CCqUC1hP6je3G62j+zww/wgtoHu4zPIayMI6weybNw8vf9zLEzTYroYAR1pmHDMsGJDsjDe7Jp83z2tzfodADi7/H0X+X4qdRKmC8OG9znm9DJl6ILkMrxX3sEvRCx86l7+87f5pWok6ivdBGcq9qncgBXBQ9F3XNPbNjvxaSg7CNDAwPLny3g0nj4OCFnSsLv89lkv3AGV2MRtD73SJowFgXnrjZjjy7c2lpKpt+0GXitWgTdG3l8ZbTd6XJVyl8g9IaxoMFB9Zj6E9YPCLvSeQIw98fmf+289nu+aLz0L5gALPMAAbY19XWOb+Eh/TfwHsTDwNLUfMSHYlEIpFIJBKJRCJ/G78B/xjl1MSF/gEAAAAASUVORK5CYII=>

[image71]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADEAAAAZCAYAAACYY8ZHAAACT0lEQVR4Xu2WS4iOURjHH4ySzLiUBg2Ru8xESC4lSiILCwkpibDEzkjZySW2wlKJBdNYoGbCyi2SlQ2S20KZGrlF+P97zut75j/v+xG+xej916/O8z9P55znPZfvMytV6lc6As6kdifoAsMr3X1DN8F3MAYcTe1VPTL6gBaB7al9HnwF4yrd+RoGZoPD4Jb0ZdoKvoEDYBA4ZD541AbzrWfuDvDG/CvWxSTRZPBRTWgUuAROg4HSlytOxMkfWXERn0C7eNdBY4g/gI0hnm8+9r7gRfUD18xzinTV/Hg1aIdqLBgAdllxEZxoi3i7wf4QPzZfWNQV8x3pLz61DTy36kWsNe8/qB1FKiqi3nygeeIvA5+tclyYQ2b9zPBdoDcleJnYx1wtgvGd1F6X4pOV7uoqKqLZfKAW8RcnnztJPQFt1vMOnAPvrfe5Xp28vCKegc2pfRl0m9+d31JREdliZ4q/MPnxy0eNAO/AcfGHgKepnVfEJHAR3DO/hzpvVbGI22qaH5u8IhYkX48ZxQK/gBfiM5dfOruoeUX8lVhEdhajsldGjxPfc/ozxKdemx+vieI/AGtCXJMi7qoJNZlPNFf8pckfKj4fgodgtPjUBYlrUgTPYZ440SbxdoKz4p0yf9ej+PuRFTpN2GM+dhYPTnl/LBZxX80kTnRMPC54RYhbwSuw0vwxWAKWg5chR7Xe/tFO8LUYCU6YX7rp1vsX8gZ4C8aneKr5yxPFvyVckNIRk4K4O3vNcyaYr4M/ujUXvy53bI52lCpVqlSp/0o/AAV6hDjYJ7z5AAAAAElFTkSuQmCC>

[image72]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADEAAAAZCAYAAACYY8ZHAAACsklEQVR4Xu2WW4hOURTHFyG5exi3XCYRaUxySa5fSOJNuZSUJs2keBiX8kJ5IrmUN7cSKUKUax7kUlIk5YEkJMmDQpSQ8P9/a+3Z69uzx3yRMnV+9a+9/muf/Z11ztr7fCIFBe2xCzpu42vQe6h/THcM7kA/oSHQbhsvqpjRAZgBNdn4FPQdGh7T7bNStPKLib8a+gFtg7pDO0UX90yG3kG3ROc0i66VY6PoWoOhXtATqJvLD4IuQIehrs6vireSL+ILdD7xbkADXfwa+goNcN45aKKLyQapLG6Wxek8clW0vfqkid/xSvJF0GtIvPXQVhdzDn/Q0wgddfFI6DP02HmzRd/yWOcFloiuuyNN5OgBPZfYAr6I3uZNcR6ZK/rku1jMOWdiukzJ/FEWhze9tGVGa5i/a+NlFh+M6bbhKXBA8kWMN6/eeWSm+cMs5vhsTJdhofTnW8wxxaf/DPoA3bZc4CW0ysZXoI/Q6JjOw15kG/WTfBHhZuucR6abP8Fiji/FdJnl5vOJklAEN39nqCd0zOUJ3xr30n3RfZj+bha/YXNFhKeZLjbN/NBmPJnY7zxtCG+Spw7nLDYvFLHG4gC97YlXNSMktgPJFTHVvLSdeJ7TH2cxP0jfRM927rF90GmbwzVIKKJkcYDevcSrmstJnCtiqHn8DnjmmN/XeXwrbKlH0Dpogej3hG1DQhHpcUrvReJVRSfRY83rpOiC1y0O0OOH0MOWOOHiTSa2UYCHxQoXPxRda6HzCL0jiffH7JfWb4LQ25t4h0SfdCA8Ze4hwoOC+8QXFT50W5xH6LE9/xpuSG5yLshzOmxQclP0hmotHgN9askqvO4BVCN6Ld8mr/Hw78hT6I3z+D9pj4v/OSXRfTMpTRg8btdC80TbtS34gdwsOre2MlVQUFBQ8B/wC3W1qwoiOIlmAAAAAElFTkSuQmCC>

[image73]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADsAAAAaCAYAAAAJ1SQgAAACOUlEQVR4Xu2WTYhOYRTHz/jM94jFKDOsWKCxodiQmoVRMhtTJCtWKCVFshqTnQ0bYkFoVsNCjY+NFWYlZEFigWkKSSHl6//v3Kc593Tv6z73lpp6fvXr7Z5z7sd53ud57hVJJBKJScpy+CezM5/KcRl2+2BDFsIz8AsccbnAEFwHp8O18Dfcl6uIhI2+8kHHfvhSyh8qlpui932R/RZdt1c0N9XEePwddphYFLzARR8sgDfdBR/CHbAtn46iCy6FJ6S82QHRXI+JhVnYb2KVmSZ6Mm8cyxb4Bh6Es/KpyrRqloO53cVY+w0udvFCFoiO2Gd4H+4UnZ51WQ9vwHE43+Wq0KpZD2cWa0/7RBGrRP+Jx3AKHIQ/4XlTUxde+4PoQMY0XaVZPiun/QV4RfJruBRe9JQ55hTmTrjExOqwGd6BByR+OldpNrACfoTbfMKzWvSia0xsQxarC9fUA/gc7nW5qoRmb/tECaz9Bbf6hOUkfO1ix6Ves2FXfgr7pNmuHNvsV9H6Jz5huQqvu9hdiW92pug7medyN25KaJbLwHMIDrvYO9H6ls99GB41x8dET3gGd8NrJlfEe3gJrvSJhoRmOXiWRVncNxVifJZS2uGo6AYyGz6CP0SnIuMbJ0oLqfMebsUMOFf0MzQM+jzJb3CcjWPmmLCWA//PTfUe/CQ6FfituQe+hUds0X/irEz8S1a+FgNzRAfjFjwn+l3Atb3M1CSawhGv6qbsnEkL39NV5XpMJBKJhOUv46iMQ6bvgbMAAAAASUVORK5CYII=>