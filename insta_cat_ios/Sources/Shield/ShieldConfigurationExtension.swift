import ManagedSettings
import ManagedSettingsUI
import UIKit

/// 인스타를 열었을 때 대신 뜨는 화면. 폭발 고양이가 등장하는 자리입니다.
///
/// 주의: iOS 는 이 화면에 **정지 이미지만** 넣을 수 있습니다. 동영상도 GIF 도 안 됩니다.
/// 그래서 화면이 다시 그려질 때마다(= 인스타를 열 때마다, "한 번 더 터뜨리기" 를 누를 때마다)
/// 폭발 프레임을 한 칸씩 넘겨 불이 계속 다르게 타오르는 것처럼 보이게 했습니다.
/// 부드럽게 이어지는 애니메이션은 앱 안에서만 볼 수 있습니다.
final class ShieldConfigurationExtension: ShieldConfigurationDataSource {

    override func configuration(shielding application: Application) -> ShieldConfiguration {
        explosionShield()
    }

    override func configuration(shielding application: Application,
                                in category: ActivityCategory) -> ShieldConfiguration {
        explosionShield()
    }

    override func configuration(shielding webDomain: WebDomain) -> ShieldConfiguration {
        explosionShield()
    }

    override func configuration(shielding webDomain: WebDomain,
                                in category: ActivityCategory) -> ShieldConfiguration {
        explosionShield()
    }

    // MARK: -

    private func explosionShield() -> ShieldConfiguration {
        // 짤을 못 찾으면 직접 그리는 고양이로 대체합니다.
        let icon = ExplosionCat.advanceFrame()
            ?? CatArt.image(pose: .stern, size: CGSize(width: 180, height: 180))

        return ShieldConfiguration(
            backgroundBlurStyle: .systemUltraThinMaterialDark,
            backgroundColor: UIColor(red: 0.09, green: 0.07, blue: 0.10, alpha: 0.94),
            icon: icon,
            title: ShieldConfiguration.Label(text: ExplosionCat.taunt, color: .white),
            subtitle: ShieldConfiguration.Label(text: subtitle(),
                                               color: UIColor.white.withAlphaComponent(0.78)),
            primaryButtonLabel: ShieldConfiguration.Label(
                text: "알겠다먀 (닫기)",
                color: UIColor(red: 0.10, green: 0.08, blue: 0.11, alpha: 1)),
            primaryButtonBackgroundColor: UIColor(red: 0.98, green: 0.62, blue: 0.20, alpha: 1),
            secondaryButtonLabel: ShieldConfiguration.Label(
                text: "한 번 더 터뜨리기 🔥",
                color: UIColor.white.withAlphaComponent(0.85))
        )
    }

    private func subtitle() -> String {
        let limit = Settings.limitMinutes
        guard let remaining = Settings.minutesUntilRelease, remaining > 0 else {
            return "인스타 \(limit)분 다 썼다먀. 곧 풀어줄게."
        }
        return "인스타 \(limit)분 다 썼다먀.\n\(remaining)분 뒤에 다시 보자."
    }
}
