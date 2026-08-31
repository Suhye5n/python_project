import SwiftUI
import Combine

/// 고양이가 실제로 움직이는 곳. 앱 안에서는 제약이 없어서 부드러운 애니메이션이 됩니다.
struct CatStage: View {

    enum Mode {
        case sleeping   // 감시 꺼짐
        case patrolling // 감시 중
        case angry      // 차단 중 — 폭발 고양이 등장

        var caption: String {
            switch self {
            case .sleeping: return "쿨쿨… 감시 꺼져 있음"
            case .patrolling: return "순찰 중 — 인스타 열면 시간 잽니다"
            case .angry: return "지금 인스타 잠겨 있음"
            }
        }
    }

    let mode: Mode

    var body: some View {
        Group {
            if mode == .angry {
                ExplosionCatView()
            } else {
                walkingCat
            }
        }
        .frame(height: 220)
        .clipShape(RoundedRectangle(cornerRadius: 24))
    }

    // MARK: - 걸어다니는 고양이

    @State private var x: CGFloat = 60
    @State private var goingRight = true
    @State private var stepFlip = false

    private let stepTimer = Timer.publish(every: 0.22, on: .main, in: .common).autoconnect()

    private var walkingCat: some View {
        GeometryReader { geo in
            ZStack(alignment: .bottomLeading) {
                LinearGradient(colors: [Color(red: 0.99, green: 0.95, blue: 0.88),
                                        Color(red: 0.96, green: 0.90, blue: 0.80)],
                               startPoint: .top, endPoint: .bottom)

                Image(uiImage: CatArt.image(pose: mode == .sleeping
                                            ? .sleep
                                            : (stepFlip ? .walkA : .walkB)))
                    .resizable()
                    .interpolation(.high)
                    .frame(width: 120, height: 120)
                    .scaleEffect(x: goingRight ? 1 : -1, y: 1)
                    .position(x: mode == .patrolling ? x : geo.size.width / 2,
                              y: geo.size.height - 68)

                Text(mode.caption)
                    .font(.footnote)
                    .foregroundStyle(.secondary)
                    .padding(12)
            }
            .onAppear {
                x = min(80, geo.size.width / 2)
                patrol(width: geo.size.width)
            }
            .onChange(of: mode) { _ in patrol(width: geo.size.width) }
        }
        .onReceive(stepTimer) { _ in
            if mode == .patrolling { stepFlip.toggle() }
        }
    }

    /// 왼쪽 끝 ↔ 오른쪽 끝을 계속 왔다 갔다 합니다.
    private func patrol(width: CGFloat) {
        guard mode == .patrolling, width > 160 else { return }
        let target: CGFloat = goingRight ? width - 70 : 70
        let duration = max(1.0, Double(abs(target - x)) / 55.0)

        withAnimation(.linear(duration: duration)) { x = target }

        DispatchQueue.main.asyncAfter(deadline: .now() + duration + 0.4) {
            goingRight.toggle()
            patrol(width: width)
        }
    }
}

/// 불이 실제로 터지듯 움직이는 폭발 고양이. 16장을 이어 붙인 루프입니다.
struct ExplosionCatView: View {

    @State private var index = 0
    private let frameTimer = Timer.publish(every: 0.09, on: .main, in: .common).autoconnect()

    var body: some View {
        ZStack {
            Color.black

            if let image = ExplosionCat.frame(index) {
                Image(uiImage: image)
                    .resizable()
                    .aspectRatio(contentMode: .fill)
            }

            VStack {
                Spacer()
                Text(ExplosionCat.taunt)
                    .font(.system(size: 18, weight: .heavy))
                    .multilineTextAlignment(.center)
                    .foregroundStyle(.white)
                    .shadow(color: .black, radius: 1)
                    .shadow(color: .black.opacity(0.9), radius: 4)
                    .padding(.bottom, 16)
                    .padding(.horizontal, 12)
            }
        }
        .onReceive(frameTimer) { _ in
            index = (index + 1) % ExplosionCat.frameCount
        }
    }
}
