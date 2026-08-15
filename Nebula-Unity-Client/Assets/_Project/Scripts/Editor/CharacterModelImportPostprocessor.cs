using UnityEditor;
using UnityEngine;

namespace Nebula.Editor
{
    /// <summary>
    /// Freezes Day-3 character import defaults for assets under
    /// Assets/_Project/Art/Characters/. Manual walkthrough first; automation second.
    /// Does not invent missing textures — FBX often ships without embedded maps.
    /// </summary>
    public sealed class CharacterModelImportPostprocessor : AssetPostprocessor
    {
        private const string CharactersRoot = "Assets/_Project/Art/Characters/";

        private bool IsCharacterModelPath =>
            assetPath.StartsWith(CharactersRoot) &&
            (assetPath.EndsWith(".fbx") || assetPath.EndsWith(".FBX"));

        private bool IsCharacterTexturePath =>
            assetPath.StartsWith(CharactersRoot) &&
            (assetPath.EndsWith(".png") || assetPath.EndsWith(".jpg") ||
             assetPath.EndsWith(".jpeg") || assetPath.EndsWith(".tga"));

        private void OnPreprocessModel()
        {
            if (!IsCharacterModelPath)
                return;

            var importer = (ModelImporter)assetImporter;

            // Model
            importer.addCollider = false;
            importer.isReadable = false;

            // Rig — static AI mesh has no skeleton
            importer.animationType = ModelImporterAnimationType.None;

            // Animation
            importer.importAnimation = false;

            // Materials — create via MaterialDescription; remap/extract stays manual when needed
            importer.materialImportMode = ModelImporterMaterialImportMode.ImportViaMaterialDescription;
            importer.materialLocation = ModelImporterMaterialLocation.InPrefab;
        }

        private void OnPreprocessTexture()
        {
            if (!IsCharacterTexturePath)
                return;

            var importer = (TextureImporter)assetImporter;
            var fileName = System.IO.Path.GetFileNameWithoutExtension(assetPath);

            // Mask / packed maps should be linear, not sRGB
            if (fileName.IndexOf("MetallicRoughness", System.StringComparison.OrdinalIgnoreCase) >= 0 ||
                fileName.IndexOf("Mask", System.StringComparison.OrdinalIgnoreCase) >= 0 ||
                fileName.IndexOf("ORM", System.StringComparison.OrdinalIgnoreCase) >= 0)
            {
                importer.sRGBTexture = false;
                importer.textureType = TextureImporterType.Default;
            }
            else if (fileName.IndexOf("Normal", System.StringComparison.OrdinalIgnoreCase) >= 0)
            {
                importer.textureType = TextureImporterType.NormalMap;
            }
            else
            {
                // BaseColor / albedo
                importer.sRGBTexture = true;
                importer.textureType = TextureImporterType.Default;
            }
        }
    }
}
