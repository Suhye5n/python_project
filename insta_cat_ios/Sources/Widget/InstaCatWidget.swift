import WidgetKit
import SwiftUI

struct CatEntry: TimelineEntry {
    let date: Date
    let isShielded: Bool
    let blockedToday: Int
    /// 위젯 안에서 고양이가 서 있을 가로 위치 (0…1). 타임라인마다 조금씩 움직입니다.
    let position: Double
    let pose: CatPose
    /// 잠금 중일 때 보여줄 폭발 프레임 번호.
    let frameIndex: Int
}

struct CatProvider: TimelineProvider {

    func placeholder(in context: Context) -> CatEntry {
        CatEntry(date: Date(), isShielded: false, blockedToday: 0,
                 position: 0.5, pose: .sit, frameIndex: 0)
    }

    func getSnapshot(in context: Context, completion: @escaping (CatEntry) -> Void) {
        completion(entry(at: Date(), step: 0))
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<CatEntry>) -> Void) {
        // 15분 간격으로 세 시간치를 미리 만들어 두면 고양이가 위젯 안을 천천히 돌아다닙니다.
        let now = Date()
        let entries = (0..<12).map { step in
            entry(at: now.addingTimeInterval(TimeInterval(step * 15 * 60)), step: step)
        }
        completion(Timeline(entries: entries, policy: .atEnd))
    }

    private func entry(at date: Date, step: Int) -> CatEntry {
        let shielded = Settings.isShielded
        // 0 → 1 → 0 을 오가는 삼각파.
        let phase = Double(step % 8) / 4.0
        let position = phase <= 1 ? phase : 2 - phase
        let pose: CatPose = shielded ? .stern : (step % 2 == 0 ? .walkA : .walkB)
        return CatEntry(date: date,
                        isShielded: shielded,
                        blockedToday: Settings.blockedToday,
                        position: position,
                        pose: pose,
                        frameIndex: step)
    }
}

struct InstaCatWidgetView: View {
    var entry: CatEntry

    private var caption: String {
        entry.isShielded ? "날려버렸다먀" : "오늘 \(entry.blockedToday)번 잡음"
    }

    var body: some View {
        GeometryReader { geo in
            ZStack(alignment: .bottomLeading) {
                if entry.isShielded, let boom = ExplosionCat.frame(entry.frameIndex) {
                    // 잠금 중일 때는 위젯도 폭발 고양이로 바뀝니다.
                    Image(uiImage: boom)
                        .resizable()
                        .aspectRatio(contentMode: .fill)
                        .frame(width: geo.size.width, height: geo.size.height)
                        .clipped()
                } else {
                    Image(uiImage: CatArt.image(pose: entry.pose))
                        .resizable()
                        .frame(width: 62, height: 62)
                        .position(x: 34 + entry.position * max(0, geo.size.width - 68),
                                  y: geo.size.height - 34)
                }

                Text(caption)
                    .font(.caption2.bold())
                    .foregroundStyle(entry.isShielded ? Color.white : Color.secondary)
                    .shadow(color: .black.opacity(entry.isShielded ? 0.9 : 0), radius: 3)
                    .padding(8)
            }
        }
        .widgetBackground(Color(red: 0.99, green: 0.95, blue: 0.88))
    }
}

@main
struct InstaCatWidget: Widget {
    var body: some WidgetConfiguration {
        StaticConfiguration(kind: "InstaCatWidget", provider: CatProvider()) { entry in
            InstaCatWidgetView(entry: entry)
        }
        .configurationDisplayName("인스타 고양이")
        .description("고양이가 홈 화면을 돌아다니며 인스타를 지켜봅니다.")
        .supportedFamilies([.systemSmall, .systemMedium])
    }
}

private extension View {
    /// iOS 17 부터는 위젯 배경을 containerBackground 로 줘야 합니다.
    @ViewBuilder
    func widgetBackground(_ color: Color) -> some View {
        if #available(iOS 17.0, *) {
            containerBackground(color, for: .widget)
        } else {
            background(color)
        }
    }
}
