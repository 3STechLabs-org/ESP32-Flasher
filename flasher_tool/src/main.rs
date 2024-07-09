use anyhow::Result;
use eframe::egui;
use espflash::cli;
use std::default;
use std::error::Error;

use espflash::cli::ConnectArgs;
use espflash::cli::FlashConfigArgs;
use espflash::elf::ElfFirmwareImage;
use espflash::flasher::FlashDataBuilder;
use espflash::targets::Chip;

use espflash::flasher::FlashFrequency;
use espflash::flasher::FlashMode;
use espflash::flasher::FlashSize;
use espflash::{cli::config::Config, targets::Esp32Target};
use espflash::{
    cli::{connect, flash_elf_image, make_flash_data},
    flasher::{FlashSettings, Flasher},
};
use std::fs::File;

use std::collections::HashSet;
use std::fs;
use std::io;
use std::path::Path;
use std::path::PathBuf;
use zip::ZipArchive;

#[non_exhaustive]
struct ESP32Flasher {
    zip_file: Option<PathBuf>,
    port: Option<String>,
    progress: f32,
    status: String,
    available_ports: Vec<String>,
}

impl ESP32Flasher {
    fn new(cc: &eframe::CreationContext<'_>) -> Self {
        let mut flasher = Self {
            zip_file: None,
            port: None,
            progress: 0.0,
            status: String::new(),
            available_ports: Vec::new(),
        };
        flasher.detect_ports();
        flasher
    }

    fn detect_ports(&mut self) {
        let mut ports = HashSet::new();
        match serialport::available_ports() {
            Ok(available_ports) => {
                for port in available_ports {
                    ports.insert(port.port_name);
                }
                self.available_ports = ports.into_iter().collect();
                self.available_ports.sort();
                println!("Detected ports: {:?}", self.available_ports);
            }
            Err(e) => {
                self.status = format!("Error detecting ports: {}", e);
                println!("{}", self.status);
            }
        }
    }

    fn browse_file(&mut self) {
        if let Some(path) = rfd::FileDialog::new().pick_file() {
            self.zip_file = Some(path);
        }
    }

    fn flash_firmware(&mut self) -> Result<(), Box<dyn Error>> {
        if let (Some(zip_file), Some(port)) = (&self.zip_file, &self.port) {
            self.status = "Extracting ZIP file...".to_string();
            match self.extract_zip(zip_file) {
                Ok(extract_path) => {
                    self.status = "Flashing firmware...".to_string();
                    self.flash_extracted_files(&extract_path, port)?;
                }
                Err(e) => self.status = format!("Error extracting ZIP: {}", e),
            }
        } else {
            self.status = "Please select both ZIP file and port.".to_string();
        }
        Ok(())
    }

    fn extract_zip(&self, zip_path: &PathBuf) -> io::Result<PathBuf> {
        let extract_path = zip_path.parent().unwrap().join("extracted");
        fs::create_dir_all(&extract_path)?;

        let file = fs::File::open(zip_path)?;
        let mut archive = ZipArchive::new(file)?;

        for i in 0..archive.len() {
            let mut file = archive.by_index(i)?;
            let outpath = extract_path.join(file.name());

            if file.name().ends_with('/') {
                fs::create_dir_all(&outpath)?;
            } else {
                if let Some(p) = outpath.parent() {
                    if !p.exists() {
                        fs::create_dir_all(p)?;
                    }
                }
                let mut outfile = fs::File::create(&outpath)?;
                io::copy(&mut file, &mut outfile)?;
            }
        }

        Ok(extract_path)
    }

    fn flash_extracted_files(
        &mut self,
        extract_path: &Path,
        port: &str,
    ) -> Result<(), Box<dyn Error>> {
        let config = Config::load()?;
        let mut connect_args = ConnectArgs {
            port: Some(port.to_string()),
            baud: Some(921600),
            before: ResetBeforeOperation::Default,
            no_stub: false,
            after: ResetAfterOperation::Default,
            chip: Chip::Esp32,
            confirm_port: false,
            force: false,
            ..Default::default()
        };

        let mut flasher = connect(&connect_args, &config, false, false)?;
        flasher.verify_minimum_revision(Chip::Esp32.into_target().chip_revision())?;

        let target_xtal_freq = espflash::targets::Esp32Target::crystal_freq(flasher.connection())?;

        let elf_path = extract_path.join("firmware.elf");
        let elf_data = fs::read(&elf_path)?;
        let elf_file = xmas_elf::ElfFile::new(&elf_data)?;
        let elf_firmware_image = ElfFirmwareImage::new(elf_file);

        let flash_config_args = FlashConfigArgs {
            flash_mode: Some(FlashMode::Dio),
            flash_freq: Some(FlashFrequency::_80Mhz),
            flash_size: Some(FlashSize::_4Mb),
            ..Default::default()
        };

        let flash_data =
            make_flash_data(elf_firmware_image, &flash_config_args, &config, None, None)?;

        flash_elf_image(&mut flasher, &elf_data, flash_data, target_xtal_freq)?;

        self.status = "Firmware flashed successfully!".to_string();
        Ok(())
    }
}

impl eframe::App for ESP32Flasher {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        if ctx.input(|i| i.time) % 5.0 < 0.1 {
            self.detect_ports();
        }

        egui::CentralPanel::default().show(ctx, |ui| {
            ui.heading("ESP32 Flasher");
            if ui.button("Browse Firmware Package").clicked() {
                self.browse_file();
            }
            if let Some(path) = &self.zip_file {
                ui.label(format!("Selected file: {}", path.display()));
            }
            egui::ComboBox::from_label("Select Port")
                .selected_text(self.port.as_deref().unwrap_or(""))
                .show_ui(ui, |ui| {
                    for port in &self.available_ports {
                        ui.selectable_value(&mut self.port, Some(port.clone()), port);
                    }
                });
            if ui.button("Flash ESP32").clicked() {
                match self.flash_firmware() {
                    Ok(_) => {}
                    Err(e) => self.status = format!("Error flashing firmware: {}", e),
                }
            }
            ui.label(&self.status);
            ui.add(egui::ProgressBar::new(self.progress));
        });
    }
}

fn main() -> eframe::Result<()> {
    let native_options = eframe::NativeOptions::default();
    eframe::run_native(
        "ESP32 Flasher",
        native_options,
        Box::new(|cc| Ok(Box::new(ESP32Flasher::new(cc)))),
    )
}
