using UnityEngine;

public class Billboard : MonoBehaviour
{
    // 每一帧都执行
    void LateUpdate()
    {
        // 单词：LookAt [lʊk æt] 看向
        // 让这个物体（Canvas）的正面永远对着主摄像机
        transform.LookAt(transform.position + Camera.main.transform.forward);
    }
}