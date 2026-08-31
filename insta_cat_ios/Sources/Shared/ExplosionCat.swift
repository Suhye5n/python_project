import UIKit

/// "내가 날려버렸다먀" 폭발 고양이 짤.
///
/// 프레임은 `Resources/Explosion/explosion_00.jpg` … `_15.jpg` 로 번들에 들어 있고
/// `tools/make_frames.py` 로 다시 만들 수 있습니다.
enum ExplosionCat {

    static let frameCount = 16

    static let taunt = "니 미래에 방해가 되는 인스타는\n내가 날려버렸다먀"

    static func frame(_ index: Int) -> UIImage? {
        let i = ((index % frameCount) + frameCount) % frameCount
        return UIImage(named: String(format: "explosion_%02d", i))
    }

    /// 잠금 화면(Shield)은 정지 이미지만 넣을 수 있습니다.
    /// 그래서 화면이 다시 그려질 때마다 다음 프레임으로 넘겨, 열 때마다 불이 다르게 타오르게 합니다.
    static func advanceFrame() -> UIImage? {
        Settings.shieldFrame += 1
        return frame(Settings.shieldFrame)
    }
}
