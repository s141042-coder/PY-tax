import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from tax_logic import calculate_tax

# 設定 Log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# 允許跨域請求 (提供前端網頁串接)
CORS(app)

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "status": "success",
        "message": "Taiwan Tax Calculation API is running.",
        "endpoints": {
            "health_check": "/healthz",
            "calculate_tax": "/api/v1/tax/calculate [POST]"
        }
    }), 200

@app.route("/healthz", methods=["GET"])
def health_check():
    """ Render 部署專用的健康檢查端點 """
    return jsonify({"status": "healthy"}), 200

@app.route("/api/v1/tax/calculate", methods=["POST"])
def tax_calculate_endpoint():
    """ 綜合所得稅試算 API 端點 """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "message": "無效的 JSON 請求內容"
            }), 400

        # 資料型態檢查與計算
        result = calculate_tax(data)
        
        return jsonify({
            "status": "success",
            "data": result
        }), 200

    except TypeError as te:
        logger.error(f"資料型態錯誤: {str(te)}")
        return jsonify({"status": "error", "message": f"參數型態有誤: {str(te)}"}), 400
    except Exception as e:
        logger.error(f"伺服器內部錯誤: {str(e)}")
        return jsonify({"status": "error", "message": "伺服器處理時發生錯誤，請檢查輸入參數"}), 500

if __name__ == "__main__":
    # 本地開發測試埠號配置
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
  
