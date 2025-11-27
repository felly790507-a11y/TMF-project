import logging
import shioaji as sj

logger = logging.getLogger(__name__)

class ShioajiClient:
    def __init__(self, config):
        self.config = config
        self.simulation = config.get("simulation", True)
        self.api = sj.Shioaji(simulation=self.simulation)

    def login(self):
        try:
            self.api.login(
                api_key=self.config["api_key"],
                secret_key=self.config["secret_key"],
                contracts_timeout=10000
            )
            logger.info("登入成功｜模式：%s", "模擬" if self.simulation else "真實")
        except Exception as e:
            logger.exception("Shioaji 登入失敗")
            raise

    def activate_ca_if_needed(self):
        if not self.simulation:
            self.api.activate_ca(
                ca_path=self.config["ca_path"],
                ca_passwd=self.config["ca_passwd"],
                person_id=self.config["person_id"]
            )
            logger.info("憑證啟用成功")

    def select_tmf_contract(self):
        # 選擇最近到期且非 R1/R2 的 TMF 合約
        contracts = [c for c in self.api.Contracts.Futures.TMF]
        candidates = [x for x in contracts if x.code[-2:] not in ["R1","R2"]]
        if not candidates:
            raise RuntimeError("找不到 TMF 合約")
        contract = min(candidates, key=lambda x: x.delivery_date)
        logger.info("選擇合約：%s", contract.code)
        return contract
