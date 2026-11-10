# ViVu — Website đặt vé xe liên tỉnh

Đồ án IE104 — Internet và Công nghệ Web. Giao diện xanh ngọc #09B587, trắng và cam #FFA509, tương thích máy tính và điện thoại. Logo xe khách và chuông thông báo bằng SVG.

## Chạy trên Windows

1. Gửi nguyên file ZIP cho máy nhận và giải nén toàn bộ thư mục trước khi chạy. Không gửi riêng CHAY-WEB.bat và không mở trực tiếp trong cửa sổ xem ZIP.
2. Nhấp đúp **CHAY-WEB.bat**, giữ cửa sổ đang chạy.
3. Trình duyệt mở sau khi máy chủ sẵn sàng. Nếu không tự mở, truy cập http://localhost:8000.

Yêu cầu Python 3.10 trở lên. Không cần cài thư viện, Node.js, XAMPP hoặc kết nối mạng. Tập tin chạy nhận cả Python của Codex trên máy hiện tại. Máy khác có thể cài Python từ python.org.

Chạy thủ công: python -X utf8 server.py. Đổi cổng nếu 8000 bị chiếm: python -X utf8 server.py --port 8001 rồi mở http://localhost:8001.

## Tài khoản trình diễn

| Vai trò | Email | Mật khẩu |
|---|---|---|
| Quản trị | admin@vivu.vn | Admin@123 |
| Khách hàng | khach@vivu.vn | Khach@123 |

Có thể tự đăng ký. Thông tin tài khoản mẫu là dữ liệu minh họa. Chưa có gửi email/SMS.

## Chức năng

- Tìm vé một chiều/khứ hồi theo tuyến, ngày, 1–6 hành khách; đổi chiều hành trình.
- Tìm tên nhà xe có gợi ý, hỗ trợ nhập một phần tên, không phân biệt hoa thường và dấu. Lọc giờ khởi hành theo 8 khoảng 3 giờ: 00–03, 03–06, 06–09, 09–12, 12–15, 15–18, 18–21, 21–24. Đầu khoảng được tính, cuối khoảng thuộc khoảng kế tiếp. Có thể kết hợp tìm nhà xe với khoảng giờ và sắp xếp theo giá/thời gian.
- Chọn ghế khoang A/B, điểm đón; kiểm tra số lượng ghế cả ở giao diện và máy chủ.
- Đăng ký, đăng nhập, sửa hồ sơ, đăng xuất; phiên hết hạn sau 2 ngày.
- Nhập liên hệ, mã VIVU10 giảm 10%, tối đa 100.000đ; máy chủ tự tính tiền.
- Thanh toán tại nhà xe hoặc trực tuyến mô phỏng, không thu tiền.
- Mã vé, lịch sử, tra cứu bằng mã và số điện thoại, in/lưu PDF bằng hộp thoại trình duyệt.
- Hủy cả đơn trước khởi hành sớm nhất ít nhất 2 giờ; giải phóng ghế.
- Quản trị: thống kê giá trị đơn xác nhận, tìm đơn, xuất CSV, xem khách hàng, thêm chuyến, sửa giá, ẩn/mở chuyến chưa có ghế đặt.
- SQLite lưu bền vững, giao dịch và khóa chính (trip_id, seat) ngăn đặt trùng.

## Dữ liệu mẫu

Tự tạo 91 ngày lịch trình, 40 cặp tuyến hai chiều, mỗi chiều 12 chuyến/ngày: tổng cộng 960 chuyến/ngày, hơn 87.000 lịch khởi hành.

26 địa điểm trải dài từ miền Tây, miền Nam, Tây Nguyên, miền Trung đến miền Bắc; có các tuyến TP. Hồ Chí Minh ↔ Cà Mau / Quy Nhơn / Phan Thiết / Buôn Ma Thuột, Hà Nội ↔ Sa Pa / Hà Giang / Hạ Long / Hải Phòng và nhiều tuyến khác.

Khung giờ: 00:30, 05:00, 06:30, 08:00, 09:30, 11:00, 12:30, 14:30, 16:00, 18:30, 20:00, 22:00. Có 5 nhà xe mẫu, loại Limousine 24 phòng và giường nằm 36 chỗ. Giá, nhà xe, điểm đón và thời lượng phục vụ học tập. Khởi động lại chỉ bổ sung lịch còn thiếu; giữ nguyên tài khoản, đơn, giá và trạng thái lịch đã có.

Tên góc phải của admin luôn là **Quản trị**. Khách hàng hiện tên đầy đủ đã đăng ký, có lời chào riêng ở trang chủ và được cập nhật ngay khi sửa hồ sơ. Tài khoản khách mẫu dùng nhãn **Khách trải nghiệm**; người dùng nên đăng ký tài khoản riêng để sử dụng tên của mình.

Dữ liệu ở data/vivu.db. Sao lưu khi máy chủ đã dừng. Biến môi trường VIVU_DB cho phép chọn cơ sở dữ liệu khác.

## Kịch bản trình diễn

1. Đăng nhập khách hoặc đăng ký.
2. Tìm TP. Hồ Chí Minh → Đà Lạt, ngày mai, 2 hành khách.
3. Chọn chuyến 14:30, A01 và A02, điểm đón.
4. Áp VIVU10, thanh toán mô phỏng, xác nhận: 2 × 280.000đ − 56.000đ = 504.000đ.
5. Xem mã vé, lịch sử, in PDF và tra cứu mã với số điện thoại.
6. Hủy vé rồi kiểm tra ghế trống trở lại.
7. Thử khứ hồi với ngày về sau ngày đi, chọn ghế cả hai chiều.
8. Đăng xuất, đăng nhập quản trị → Tài khoản → Trang quản trị. Thử thêm chuyến, sửa giá, ẩn/mở, xuất CSV.

## Kiểm thử và cấu trúc

Chạy python -X utf8 test_api.py. 23 bài kiểm tra dùng cơ sở dữ liệu tạm riêng: đặt đồng thời, hoàn tác đơn sai, phân quyền, giảm giá, khứ hồi, hủy vé, hồ sơ, đăng xuất. Kết quả ở docs/test-results.txt. Kiểm tra thêm bộ lọc bằng node test_filters.cjs nếu có Node.js: 16 kiểm tra tên nhà xe, dấu tiếng Việt, tám khoảng giờ và các mốc chuyển khoảng; kết quả ở docs/test-filter-results.txt. Node.js chỉ dùng cho kiểm tra này, không bắt buộc để chạy website.

- server.py: HTTP, API, xác thực, nghiệp vụ, SQLite, dữ liệu mẫu.
- public/: HTML, CSS, JavaScript.
- test_api.py: kiểm thử tích hợp.
- docs/: ảnh, báo cáo Word, kết quả kiểm thử.
- CHAY-WEB.bat: chạy nhanh Windows.

## Phạm vi

Bản hoàn chỉnh phục vụ đồ án cục bộ. Chưa kết nối nhà xe thật, ngân hàng, email/SMS, giữ ghế có thời hạn, hoàn tiền hoặc phục hồi mật khẩu. Trước triển khai công khai cần tài khoản riêng, HTTPS, giới hạn truy cập, quản lý bí mật và dịch vụ vận tải/thanh toán hợp lệ. Không dùng http.server trực tiếp cho thương mại.

Báo cáo bám bố cục mẫu, bổ sung dữ liệu và kiểm thử. Điền họ tên, MSSV, lớp, giảng viên và phân công thực tế trước khi nộp.

## Bản cập nhật lịch trình và tên hiển thị

Đóng cửa sổ máy chủ cũ và chạy lại CHAY-WEB.bat, sau đó tải lại trình duyệt để dùng phiên bản mới. Cơ sở dữ liệu trước khi bổ sung lịch trên máy hiện tại được sao lưu thành data/vivu-before-expansion.db. Báo cáo Word trong gói đã được làm lại theo phiên bản mở rộng: 22 trang, 26 địa điểm, 40 cặp tuyến hai chiều, 960 chuyến/ngày, lịch 91 ngày, tên tài khoản theo hồ sơ và 23 bài kiểm thử. Các ảnh giao diện trong báo cáo được chụp lại từ phiên bản mới.

## Bài thuyết trình

Bộ 30 slide xanh–trắng–cam có ảnh giao diện, sơ đồ chỉnh sửa được và ghi chú thuyết trình. File: Thuyet-trinh/ViVu-IE104-30-slide.pptx (tại thư mục gốc gói). Canva: https://www.canva.com/d/jZiUQ61lgOIdifH

Báo cáo Word đã bỏ tài liệu tham khảo.

## Gửi cho máy khác

Gửi ViVu-Gui-ban-be.zip tại thư mục gốc đồ án. Máy nhận giải nén toàn bộ gói, cài Python 3.10 trở lên nếu chưa có, rồi mở vivu/CHAY-WEB.bat. Không gửi riêng file .bat. Gói này gồm mã nguồn và hướng dẫn, không kèm tài khoản/đơn cá nhân đang có trên máy gửi. Lần chạy đầu sẽ tạo dữ liệu mẫu mới.

localhost là máy đang mở website. Một địa chỉ localhost đang chạy trên máy gửi không tự truy cập được từ máy khác. Muốn bạn bè chỉ bấm một đường dẫn mà không cài đặt thì cần triển khai website lên máy chủ.
