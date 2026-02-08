package org.example.server.service.impl;

import jakarta.servlet.http.HttpServletResponse;
import org.example.server.common.config.Config;
import org.example.server.common.config.ServerConfig;
import org.example.server.common.utils.DateUtils;
import org.example.server.domain.DetectionTask;
import org.example.server.mapper.DetectionTaskMapper;
import org.example.server.mapper.HsiFileMapper; // 1. 引入 HsiFileMapper
import org.example.server.service.IReportService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import com.itextpdf.text.*;
import com.itextpdf.text.pdf.*;

import java.util.HashMap;
import java.util.Map;

@Service
public class ReportService implements IReportService {

    @Autowired
    private DetectionTaskMapper detectionTaskMapper;

    @Autowired
    private HsiFileMapper hsiFileMapper; // 2. 注入 Mapper

    /*
     * 生成光谱可视化
     * */
    @Override
    public Map<String, Object> getCubeView(String matPath) {
        String absoluteMatPath = Config.getabsolutePath(matPath);
        Map<String, Object> request = new HashMap<>();
        request.put("path", absoluteMatPath);
        return ServerConfig.getResponse("/visual/cube-heavy", request);
    }

    /**
     * 生成 PDF 报告的核心逻辑
     */
    @Override
    public void exportPdf(DetectionTask task, HttpServletResponse response) {
        try {
            // 3. 补全 GT 文件信息 (如果 ID 存在但对象为空)
            if (task.getGtFileId() != null && task.getGtFile() == null) {
                task.setGtFile(hsiFileMapper.selectById(task.getGtFileId()));
            }

            // 设置响应头
            response.setContentType("application/pdf");
            String fileName = "Report_" + task.getTaskId() + ".pdf";
            response.setHeader("Content-Disposition", "attachment; filename=\"" + fileName + "\"");

            // 创建文档
            Document document = new Document(PageSize.A4);
            PdfWriter.getInstance(document, response.getOutputStream());
            document.open();

            // 字体设置
            BaseFont bfChinese = BaseFont.createFont("STSong-Light", "UniGB-UCS2-H", BaseFont.NOT_EMBEDDED);
            Font titleFont = new Font(bfChinese, 18, Font.BOLD);
            Font subTitleFont = new Font(bfChinese, 14, Font.BOLD);
            Font textFont = new Font(bfChinese, 10, Font.NORMAL);
            // Font redFont = new Font(bfChinese, 10, Font.NORMAL, BaseColor.RED);

            // --- 内容编写 ---

            // 标题
            Paragraph title = new Paragraph("高光谱目标检测任务评估报告", titleFont);
            title.setAlignment(Element.ALIGN_CENTER);
            document.add(title);
            document.add(new Paragraph("\n"));

            // 基础信息表格
            PdfPTable infoTable = new PdfPTable(4);
            infoTable.setWidthPercentage(100);
            infoTable.setSpacingBefore(10f);

            addCell(infoTable, "任务编号", subTitleFont);
            addCell(infoTable, String.valueOf(task.getTaskId()), textFont);
            addCell(infoTable, "数据文件名", subTitleFont);
            addCell(infoTable, task.getTaskName() != null ? task.getTaskName() : "N/A", textFont);

            addCell(infoTable, "检测算法", subTitleFont);
            addCell(infoTable, "DMSSN-Net", textFont);
            addCell(infoTable, "生成时间", subTitleFont);
            addCell(infoTable, DateUtils.dateTimeNow(), textFont);

            document.add(infoTable);
            document.add(new Paragraph("\n"));

            // 核心指标
            Paragraph metricTitle = new Paragraph("核心性能指标评测", subTitleFont);
            document.add(metricTitle);

            PdfPTable metricTable = new PdfPTable(5);
            metricTable.setWidthPercentage(100);
            metricTable.setSpacingBefore(10f);
            String[] headers = {"MAE", "F1-Score", "Recall", "Precision", "AUC"};
            for (String h : headers) addCell(metricTable, h, subTitleFont, BaseColor.LIGHT_GRAY);

            addCell(metricTable, String.format("%.4f", task.getMae()), textFont);
            addCell(metricTable, String.format("%.4f", task.getF1()), textFont);
            addCell(metricTable, String.format("%.4f", task.getRec()), textFont);
            addCell(metricTable, String.format("%.4f", task.getPred()), textFont);
            addCell(metricTable, String.format("%.2f", task.getAuc()), textFont);

            document.add(metricTable);
            document.add(new Paragraph("\n"));

            // --- 插入图片 (修改为 3 列布局) ---
            Paragraph imgTitle = new Paragraph("可视化检测结果对比", subTitleFont);
            document.add(imgTitle);

            // 4. 改为 3 列 (原始 | 预测 | 真值)
            PdfPTable imgTable = new PdfPTable(3);
            imgTable.setWidthPercentage(100);
            imgTable.setSpacingBefore(15f);

            // --- 第一行：图片 ---

            // 1. 原始伪彩图
            String jpgPath = convertToLocalPath(task.getJpgFile().getStoragePath());
            Image img1 = loadImage(jpgPath);
            addImageCell(imgTable, img1, "原始图片丢失");

            // 2. 预测 Mask
            String maskPath = convertToLocalPath(task.getMaskPath());
            Image img2 = loadImage(maskPath);
            addImageCell(imgTable, img2, "预测结果丢失");

            // 3. 真值 GT (如果存在)
            if (task.getGtFile() != null) {
                String gtPath = convertToLocalPath(task.getGtFile().getStoragePath());
                Image img3 = loadImage(gtPath);
                addImageCell(imgTable, img3, "GT文件丢失");
            } else {
                imgTable.addCell(createCenterTextCell("无真值(GT)", textFont));
            }

            // --- 第二行：说明文字 ---

            imgTable.addCell(createCenterTextCell("原始伪彩图", textFont));
            imgTable.addCell(createCenterTextCell("AI预测结果", textFont));

            if (task.getGtFile() != null) {
                imgTable.addCell(createCenterTextCell("真实标签(GT)", textFont));
            } else {
                imgTable.addCell(createCenterTextCell("-", textFont));
            }

            document.add(imgTable);

            // 结语
            Paragraph footer = new Paragraph("\n\n本报告由 HSOD-BIT 智能系统自动生成。", textFont);
            footer.setAlignment(Element.ALIGN_RIGHT);
            document.add(footer);

            document.close();

        } catch (Exception e) {
            e.printStackTrace();
            throw new RuntimeException("导出PDF失败");
        }
    }

    // --- 辅助方法 ---

    // 封装添加图片单元格的逻辑
    private void addImageCell(PdfPTable table, Image img, String errorMsg) {
        if (img != null) {
            PdfPCell cell = new PdfPCell(img);
            cell.setBorder(Rectangle.NO_BORDER);
            cell.setHorizontalAlignment(Element.ALIGN_CENTER);
            cell.setVerticalAlignment(Element.ALIGN_MIDDLE);
            cell.setPadding(5); // 增加一点内边距
            table.addCell(cell);
        } else {
            // 如果图片加载失败，创建一个只有文字的单元格
            PdfPCell cell = new PdfPCell(new Paragraph(errorMsg));
            cell.setBorder(Rectangle.NO_BORDER);
            cell.setHorizontalAlignment(Element.ALIGN_CENTER);
            cell.setVerticalAlignment(Element.ALIGN_MIDDLE);
            cell.setMinimumHeight(100f); // 保持高度一致
            table.addCell(cell);
        }
    }

    // 封装创建居中文字单元格 (用于图片下方的标题)
    private PdfPCell createCenterTextCell(String text, Font font) {
        PdfPCell cell = new PdfPCell(new Paragraph(text, font));
        cell.setBorder(Rectangle.NO_BORDER);
        cell.setHorizontalAlignment(Element.ALIGN_CENTER);
        return cell;
    }

    private String convertToLocalPath(String dbPath) {
        if (dbPath == null) return null;
        return dbPath.replace("/profile", Config.getProfile());
    }

    private Image loadImage(String absolutePath) {
        try {
            if (absolutePath == null) return null;
            Image image = Image.getInstance(absolutePath);
            // 5. 调整图片大小以适应 3 列布局 (A4宽度约 595pt，除去边距每列约 160-170)
            image.scaleToFit(160, 160);
            return image;
        } catch (Exception e) {
            return null;
        }
    }

    private void addCell(PdfPTable table, String text, Font font) {
        addCell(table, text, font, null);
    }

    private void addCell(PdfPTable table, String text, Font font, BaseColor color) {
        PdfPCell cell = new PdfPCell(new Paragraph(text, font));
        cell.setPadding(8);
        cell.setHorizontalAlignment(Element.ALIGN_CENTER);
        cell.setVerticalAlignment(Element.ALIGN_MIDDLE);
        if (color != null) cell.setBackgroundColor(color);
        table.addCell(cell);
    }
}