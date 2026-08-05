using UnityEngine;
using UnityEngine.InputSystem;

namespace Nebula.Modules.Chat
{
    [RequireComponent(typeof(CharacterController))]
    public class SimplePlayerMove : MonoBehaviour
    {
        [SerializeField] private float speed = 5f;
        [SerializeField] private float rotateSpeed = 12f;
        [SerializeField] private Animator animator;
        [SerializeField] private string speedParam = "Speed";
        [SerializeField] private float speedDamping = 0.12f;

        private CharacterController _cc;
        private bool _locked;
        private static readonly int SpeedHash = Animator.StringToHash("Speed");

        private void Awake()
        {
            _cc = GetComponent<CharacterController>();
            if (animator == null)
                animator = GetComponentInChildren<Animator>();
        }

        public void SetLocked(bool locked)
        {
            _locked = locked;
            if (locked)
                SetSpeed(0f);
        }

        private void Update()
        {
            if (_cc == null || Keyboard.current == null || _locked)
            {
                SetSpeed(0f);
                return;
            }

            float h = 0f;
            float v = 0f;
            var kb = Keyboard.current;

            if (kb.aKey.isPressed || kb.leftArrowKey.isPressed) h = -1f;
            if (kb.dKey.isPressed || kb.rightArrowKey.isPressed) h = 1f;
            if (kb.sKey.isPressed || kb.downArrowKey.isPressed) v = -1f;
            if (kb.wKey.isPressed || kb.upArrowKey.isPressed) v = 1f;

            Vector3 move = new Vector3(h, 0f, v);
            float magnitude = Mathf.Clamp01(move.magnitude);
            if (magnitude > 0.01f)
            {
                move.Normalize();
                _cc.SimpleMove(move * speed);

                Quaternion targetRot = Quaternion.LookRotation(move, Vector3.up);
                transform.rotation = Quaternion.Slerp(
                    transform.rotation, targetRot, rotateSpeed * Time.deltaTime);
            }
            else
            {
                _cc.SimpleMove(Vector3.zero);
            }

            SetSpeed(magnitude);
        }

        private void SetSpeed(float value)
        {
            if (animator == null) return;

            int hash = string.IsNullOrEmpty(speedParam) || speedParam == "Speed"
                ? SpeedHash
                : Animator.StringToHash(speedParam);

            foreach (var p in animator.parameters)
            {
                if (p.nameHash == hash && p.type == AnimatorControllerParameterType.Float)
                {
                    if (speedDamping > 0f)
                        animator.SetFloat(hash, value, speedDamping, Time.deltaTime);
                    else
                        animator.SetFloat(hash, value);
                    return;
                }
            }
        }
    }
}
