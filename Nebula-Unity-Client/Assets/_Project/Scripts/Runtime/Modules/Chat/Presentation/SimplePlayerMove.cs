using UnityEngine;
using UnityEngine.InputSystem;

namespace Nebula.Modules.Chat
{
    [RequireComponent(typeof(CharacterController))]
    public class SimplePlayerMove : MonoBehaviour
    {
        [SerializeField] private float speed = 5f;

        private CharacterController _cc;

        private void Awake()
        {
            _cc = GetComponent<CharacterController>();
        }

        private void Update()
        {
            if (_cc == null || Keyboard.current == null) return;

            float h = 0f;
            float v = 0f;
            var kb = Keyboard.current;

            if (kb.aKey.isPressed || kb.leftArrowKey.isPressed) h = -1f;
            if (kb.dKey.isPressed || kb.rightArrowKey.isPressed) h = 1f;
            if (kb.sKey.isPressed || kb.downArrowKey.isPressed) v = -1f;
            if (kb.wKey.isPressed || kb.upArrowKey.isPressed) v = 1f;

            Vector3 move = new Vector3(h, 0f, v).normalized;
            _cc.SimpleMove(move * speed);
        }
    }
}
