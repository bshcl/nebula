using UnityEngine;

public class SimplePlayerMove : MonoBehaviour
{
    [SerializeField] float speed = 5f;
    CharacterController _cc;

    void Awake() => _cc = GetComponent<CharacterController>();

    void Update()
    {
        float h = Input.GetAxisRaw("Horizontal"); // A/D
        float v = Input.GetAxisRaw("Vertical");   // W/S
        Vector3 move = new Vector3(h, 0f, v).normalized;
        _cc.SimpleMove(move * speed);
    }
}