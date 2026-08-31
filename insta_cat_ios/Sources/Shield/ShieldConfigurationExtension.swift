import ManagedSettings
import ManagedSettingsUI
import UIKit

/// 인스타를 열었을 때 대신 뜨는 화면. 여기가 고양이가 등장하는 자리입니다.
final class ShieldConfigurationExtension: ShieldConfigurationDataSource {

    override func configuration(shielding application: Application) -> ShieldConfiguration {
        catShield()
    }

    override func configuration(shielding application: Application,
                                in category: ActivityCategory) -> ShieldConfiguration {
        catShield()
    }

    override func configuration(shielding webDomain: WebDomain) -> ShieldConfiguration {
        catShield()
    }

    override func configuration(shielding webDomain: WebDomain,
                                in category: ActivityCategory) -> ShieldConfiguration {
        catShield()
    }

    // MARK: -

    private func catShield() -> ShieldConfiguration {
        let pets = Settings.petCount
        // 세 번 쓰다듬으면 잠깐 기분이 풀립니다. (잠금은 그대로)
        let pose: CatPose = (pets > 0 && pets % 3 == 0) ? .happy : .stern

        return ShieldConfiguration(
            backgroundBlurStyle: .systemUltraThinMaterialDark,
            backgroundColor: UIColor(red: 0.12, green: 0.10, blue: 0.16, alpha: 0.92),
            icon: CatArt.image(pose: pose, size: CGSize(width: 180, height: 180)),
            title: ShieldConfiguration.Label(text: title(pose: pose), color: .white),
            subtitle: ShieldConfiguration.Label(text: subtitle(),
                                               color: UIColor.white.withAlphaComponent(0.75)),
            primaryButtonLabel: ShieldConfiguration.Label(
                text: "알겠다냥 (닫기)",
                color: UIColor(red: 0.12, green: 0.10, blue: 0.16, alpha: 1)),
            primaryButtonBackgroundColor: UIColor(red: 0.96, green: 0.68, blue: 0.36, alpha: 1),
            secondaryButtonLabel: ShieldConfiguration.Label(
                text: "고양이 쓰다듬기 🐾",
                color: UIColor.white.withAlphaComponent(0.85))
        )
    }

    private func title(pose: CatPose) -> String {
        pose == .happy ? "그래도 안 비켜준다냥" : "여기까지다냥"
    }

    private func subtitle() -> String {
        let limit = Settings.limitMinutes
        guard let remaining = Settings.minutesUntilRelease, remaining > 0 else {
            return "인스타 \(limit)분 다 썼어. 곧 풀어줄게."
        }
        return "인스타 \(limit)분 다 썼어.\n\(remaining)분 뒤에 다시 보자."
    }
}
