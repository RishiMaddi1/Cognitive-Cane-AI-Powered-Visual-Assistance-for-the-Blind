#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <driver/i2s.h>

// WiFi credentials
const char* ssid = "*******";
const char* password = "******";

// Server URL
const char* serverUrl = "*********/stream";  // Update with your server IP

#define SAMPLE_RATE     16000  // Highest practical for ESP32
#define I2S_CHANNEL     I2S_CHANNEL_FMT_ONLY_LEFT
#define I2S_BCK_IO      GPIO_NUM_14
#define I2S_WS_IO       GPIO_NUM_15
#define I2S_DATA_IN_IO  GPIO_NUM_32
#define I2S_NUM         I2S_NUM_0
#define CHUNK_SIZE      2048  // Bigger chunk, fewer POSTs, smoother stream

int32_t raw_samples[CHUNK_SIZE];

i2s_config_t i2s_config = {
  .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
  .sample_rate = SAMPLE_RATE,
  .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT,
  .channel_format = I2S_CHANNEL,
  .communication_format = I2S_COMM_FORMAT_I2S,
  .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
  .dma_buf_count = 8,
  .dma_buf_len = 1024,
  .use_apll = false,
  .tx_desc_auto_clear = false,
  .fixed_mclk = 0
};

i2s_pin_config_t pin_config = {
  .bck_io_num = I2S_BCK_IO,
  .ws_io_num = I2S_WS_IO,
  .data_out_num = I2S_PIN_NO_CHANGE,
  .data_in_num = I2S_DATA_IN_IO
};

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(" Connected!");

  i2s_driver_install(I2S_NUM, &i2s_config, 0, NULL);
  i2s_set_pin(I2S_NUM, &pin_config);
}

void loop() {
  size_t bytes_read;
  i2s_read(I2S_NUM, raw_samples, sizeof(raw_samples), &bytes_read, portMAX_DELAY);

  int sample_count = bytes_read / sizeof(int32_t);
  uint8_t buffer[sample_count * 2];

  for (int i = 0; i < sample_count; ++i) {
    int16_t sample16 = raw_samples[i] >> 11;  // Better quality than >>16
    buffer[i * 2] = sample16 & 0xFF;
    buffer[i * 2 + 1] = (sample16 >> 8) & 0xFF;
  }

  HTTPClient http;
  http.begin(serverUrl);
  http.addHeader("Content-Type", "application/octet-stream");

  int res = http.POST(buffer, sample_count * 2);
  if (res > 0) {
    Serial.printf("POST OK: %d\n", res);
  } else {
    Serial.printf("POST failed: %s\n", http.errorToString(res).c_str());
  }
  http.end();

  delay(10);  // Stream continuously
}
