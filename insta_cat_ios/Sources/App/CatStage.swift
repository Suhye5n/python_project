import SwiftUI
import Combine

/// 고양이가 실제로 화면을 돌아다니는 곳. (앱 안에서만 가능합니다 — 아래 README 참고)
struct CatStage: View {

    enum Mode {
        case sleeping   // 감시 꺼짐
        case patrolling // 감시 중
        case angry      // 차단 중

        var caption: String {
            switch self {
            case .sleeping: return "쿨쿨… 감시 꺼져 있음"
            case .patrolling: return "순찰 중 — 인스타 열면 시간 잽니다"
            case .angry: return "여기까지! 지금은 인스타 잠겨 있어요"
            }
        }
    }

    let mode: Mode

    @State private var x: CGFloat = 60
    @State private var goingRight = true
    @State private var stepFlip = false

    private let stepTimer = Timer.publish(every: 0.22, on: .main, in: .common).autoconnect()

    private var pose: CatPose {
        switch mode {
        case .sleeping: return .sleep
        case .angry: return .stern
        case .patrolling: return stepFlip ? .walkA : .walkB
        }
    }

    var body: some View {
        GeometryReader { geo in
            ZStack(alignment: .bottomLeading) {
                RoundedRectangle(cornerRadius: 24)
                    .fill(LinearGradient(colors: [Color(red: 0.99, green: 0.95, blue: 0.88),
                                                  Color(red: 0.96, green: 0.90, blue: 0.80)],
                                         startPoint: .top, endPoint: .bottom))

                Image(uiImage: CatArt.image(pose: pose))
                    .resizable()
                    .interpolation(.high)
                    .frame(width: 120, height: 120)
                    .scaleEffect(x: goingRight ? 1 : -1, y: 1)
                    .position(x: mode == .patrolling ? x : geo.size.width / 2,
                              y: geo.size.height - 62)

                Text(mode.caption)
                    .font(.footnote)
                    .foregroundStyle(.secondary)
                    .padding(12)
            }
            .onAppear {
                x = min(80, geo.size.width / 2)
                if mode == .patrolling { patrol(width: geo.size.width) }
            }
            .onChange(of: mode) { newMode in
                if newMode == .patrolling { patrol(width: geo.size.width) }
            }
        }
        .frame(height: 200)
        .onReceive(stepTimer) { _ in
            if mode == .patrolling { stepFlip.toggle() }
        }
    }

    /// 왼쪽 끝 ↔ 오른쪽 끝을 계속 왔다 갔다 합니다.
    private func patrol(width: CGFloat) {
        guard mode == .patrolling, width > 160 else { return }
        let target: CGFloat = goingRight ? width - 70 : 70
        let distance = abs(target - x)
        let duration = max(1.0, Double(distance) / 55.0)

        withAnimation(.linear(duration: duration)) { x = target }

        DispatchQueue.main.asyncAfter(deadline: .now() + duration + 0.4) {
            goingRight.toggle()
            patrol(width: width)
        }
    }
}
