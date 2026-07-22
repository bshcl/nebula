using UnityEngine;

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
            if (_cc == null) return;

            float h = 0f;
            float v = 0f;
            if (Input.GetKey(KeyCode.A) || Input.GetKey(KeyCode.LeftArrow)) h = -1f;
            if (Input.GetKey(KeyCode.D) || Input.GetKey(KeyCode.RightArrow)) h = 1f;
            if (Input.GetKey(KeyCode.S) || Input.GetKey(KeyCode.DownArrow)) v = -1f;
            if (Input.GetKey(KeyCode.W) || Input.GetKey(KeyCode.UpArrow)) v = 1f;

            Vector3 move = new Vector3(h, 0f, v).normalized;
            _cc.SimpleMove(move * speed);
        }
    }
}
