using System.Collections.Generic;
using Nebula.Modules.Chat;
using Nebula.Modules.Inventory;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Nebula.Editor.Tools
{
    /// <summary>
    /// Lifts the scene-authored UI into Prefabs/UI and reconnects the scene objects
    /// as instances. After this, UI edits are prefab edits instead of scene-YAML edits.
    ///
    /// Cross-scene references (a panel pointing at the scene's NebulaManager) stay on
    /// the instance as an override; the prefab asset itself holds null there. Dropping
    /// one of these prefabs into a fresh scene means rewiring those fields by hand.
    /// </summary>
    public static class UiPrefabExtractor
    {
        private const string PrefabDir = "Assets/_Project/Prefabs/UI";

        [MenuItem("Nebula/Project/Extract UI Prefabs")]
        public static void Extract()
        {
            if (!AssetDatabase.IsValidFolder(PrefabDir))
            {
                Debug.LogError($"[PrefabExtractor] {PrefabDir} is missing. " +
                               "Run Nebula/Project/Migrate Folder Structure first.");
                return;
            }

            var targets = new List<GameObject>();

            // Slot template goes first so the panel ends up containing a nested prefab.
            AddByComponent<InventorySlotUI>(targets);
            AddByComponent<InventoryPanelUI>(targets);
            AddByComponent<ChatWindowUI>(targets);
            AddByName(targets, "InteractMenu");
            AddByName(targets, "InteractPrompt");

            if (targets.Count == 0)
            {
                Debug.LogWarning("[PrefabExtractor] Nothing found in the open scene.");
                return;
            }

            int saved = 0;
            foreach (var target in targets)
            {
                if (PrefabUtility.IsPartOfPrefabInstance(target))
                {
                    Debug.Log($"[PrefabExtractor] skip {target.name}: already a prefab instance");
                    continue;
                }

                string path = $"{PrefabDir}/{target.name}.prefab";
                var asset = PrefabUtility.SaveAsPrefabAssetAndConnect(
                    target, path, InteractionMode.UserAction, out bool success);

                if (success && asset != null)
                {
                    saved++;
                    Debug.Log($"[PrefabExtractor] saved {path}");
                }
                else
                {
                    Debug.LogError($"[PrefabExtractor] failed to save {target.name} -> {path}");
                }
            }

            if (saved > 0)
            {
                EditorSceneManager.MarkSceneDirty(EditorSceneManager.GetActiveScene());
                EditorSceneManager.SaveOpenScenes();
                AssetDatabase.SaveAssets();
                AssetDatabase.Refresh();
            }

            Debug.Log($"[PrefabExtractor] {saved}/{targets.Count} prefab(s) written to {PrefabDir}");
        }

        private static void AddByComponent<T>(List<GameObject> targets) where T : Component
        {
            var found = Object.FindObjectsByType<T>(
                FindObjectsInactive.Include, FindObjectsSortMode.None);

            foreach (var component in found)
            {
                var go = component.gameObject;
                if (!targets.Contains(go))
                    targets.Add(go);
            }
        }

        private static void AddByName(List<GameObject> targets, string name)
        {
            var all = Object.FindObjectsByType<Transform>(
                FindObjectsInactive.Include, FindObjectsSortMode.None);

            foreach (var transform in all)
            {
                if (transform.name != name)
                    continue;

                if (!targets.Contains(transform.gameObject))
                    targets.Add(transform.gameObject);
            }
        }
    }
}
